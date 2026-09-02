// Package colofonmcp exposes Colofon's verified document factory over MCP.
package colofonmcp

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

const maxCommandOutput = 1024 * 1024

const instructions = "Call colofon_describe before authoring to discover the current " +
	"document and book schemas. Keep every source path relative to the configured workspace, " +
	"lint Markdown before building, and write PDF outputs only below build/. Successful builds " +
	"must report verified=true with pdfua1, typst_pdfua1, and copy_safe all passing."

// Version is the Colofon release implemented by this server.
const Version = "0.2.1"

type DocumentInput struct {
	Source string `json:"source" jsonschema:"Markdown source path, relative to the configured workspace"`
	Output string `json:"output,omitempty" jsonschema:"Optional PDF output below build/, relative to the configured workspace"`
}

type BookInput struct {
	Source string `json:"source" jsonschema:"book.yaml path, relative to the configured workspace"`
	Output string `json:"output,omitempty" jsonschema:"Optional PDF output below build/, relative to the configured workspace"`
}

type LintInput struct {
	Sources []string `json:"sources" jsonschema:"Markdown source paths, relative to the configured workspace"`
}

type DescribeInput struct{}

// Runner validates all paths and delegates work to Colofon's machine-facing CLI.
type Runner struct {
	workspace string
	cli       string
	timeout   time.Duration
	mu        sync.Mutex
}

// NewRunner creates a workspace-confined Colofon command runner.
func NewRunner(workspace, cli string, timeout time.Duration) (*Runner, error) {
	if timeout <= 0 {
		return nil, errors.New("timeout must be positive")
	}
	root, err := filepath.Abs(workspace)
	if err != nil {
		return nil, fmt.Errorf("resolve workspace: %w", err)
	}
	root, err = filepath.EvalSymlinks(root)
	if err != nil {
		return nil, fmt.Errorf("resolve workspace symlinks: %w", err)
	}
	info, err := os.Stat(root)
	if err != nil || !info.IsDir() {
		return nil, fmt.Errorf("workspace is not a directory: %s", root)
	}
	resolvedCLI, err := exec.LookPath(cli)
	if err != nil {
		return nil, fmt.Errorf("find Colofon CLI %q: %w", cli, err)
	}
	resolvedCLI, err = filepath.Abs(resolvedCLI)
	if err != nil {
		return nil, fmt.Errorf("resolve Colofon CLI: %w", err)
	}
	return &Runner{workspace: root, cli: resolvedCLI, timeout: timeout}, nil
}

func inside(root, path string) bool {
	rel, err := filepath.Rel(root, path)
	return err == nil && rel != ".." && !strings.HasPrefix(rel, ".."+string(os.PathSeparator))
}

func cleanRelative(path string) (string, error) {
	if path == "" {
		return "", errors.New("path is required")
	}
	if filepath.IsAbs(path) {
		return "", errors.New("absolute paths are not allowed")
	}
	clean := filepath.Clean(path)
	if clean == "." || clean == ".." || strings.HasPrefix(clean, ".."+string(os.PathSeparator)) {
		return "", errors.New("path escapes the configured workspace")
	}
	return clean, nil
}

func (r *Runner) source(path string, extensions ...string) (string, error) {
	clean, err := cleanRelative(path)
	if err != nil {
		return "", err
	}
	abs := filepath.Join(r.workspace, clean)
	resolved, err := filepath.EvalSymlinks(abs)
	if err != nil {
		return "", fmt.Errorf("resolve source: %w", err)
	}
	if !inside(r.workspace, resolved) {
		return "", errors.New("source resolves outside the configured workspace")
	}
	info, err := os.Stat(resolved)
	if err != nil || !info.Mode().IsRegular() {
		return "", errors.New("source is not a regular file")
	}
	for _, extension := range extensions {
		if strings.EqualFold(filepath.Ext(clean), extension) {
			return clean, nil
		}
	}
	return "", fmt.Errorf("source must use one of these extensions: %s", strings.Join(extensions, ", "))
}

func (r *Runner) output(path, source string) (string, error) {
	if path == "" {
		stem := strings.TrimSuffix(filepath.Base(source), filepath.Ext(source))
		path = filepath.Join("build", stem+".pdf")
	}
	clean, err := cleanRelative(path)
	if err != nil {
		return "", err
	}
	if !strings.EqualFold(filepath.Ext(clean), ".pdf") {
		return "", errors.New("output must be a PDF")
	}
	buildRoot := filepath.Join(r.workspace, "build")
	target := filepath.Join(r.workspace, clean)
	if !inside(buildRoot, target) {
		return "", errors.New("output must be below build/")
	}
	if err := os.Mkdir(buildRoot, 0o755); err != nil && !os.IsExist(err) {
		return "", fmt.Errorf("create build directory: %w", err)
	}
	resolvedBuild, err := filepath.EvalSymlinks(buildRoot)
	if err != nil {
		return "", fmt.Errorf("resolve build directory: %w", err)
	}
	if resolvedBuild != buildRoot {
		return "", errors.New("build/ must not be a symlink")
	}
	parentRelative, err := filepath.Rel(buildRoot, filepath.Dir(target))
	if err != nil {
		return "", fmt.Errorf("resolve output parent: %w", err)
	}
	current := buildRoot
	if parentRelative != "." {
		for _, component := range strings.Split(parentRelative, string(os.PathSeparator)) {
			current = filepath.Join(current, component)
			info, statErr := os.Lstat(current)
			if os.IsNotExist(statErr) {
				if mkdirErr := os.Mkdir(current, 0o755); mkdirErr != nil {
					return "", fmt.Errorf("create output directory: %w", mkdirErr)
				}
				continue
			}
			if statErr != nil {
				return "", fmt.Errorf("inspect output directory: %w", statErr)
			}
			if info.Mode()&os.ModeSymlink != 0 || !info.IsDir() {
				return "", errors.New("output path contains a symlink or non-directory")
			}
		}
	}
	if info, statErr := os.Lstat(target); statErr == nil {
		if info.Mode()&os.ModeSymlink != 0 || !info.Mode().IsRegular() {
			return "", errors.New("existing output must be a regular file, not a symlink")
		}
	} else if !os.IsNotExist(statErr) {
		return "", fmt.Errorf("inspect output: %w", statErr)
	}
	return clean, nil
}

type limitedBuffer struct {
	bytes.Buffer
	remaining int
	truncated bool
}

func (b *limitedBuffer) Write(p []byte) (int, error) {
	original := len(p)
	if len(p) > b.remaining {
		p = p[:b.remaining]
		b.truncated = true
	}
	_, _ = b.Buffer.Write(p)
	b.remaining -= len(p)
	return original, nil
}

func (r *Runner) command(ctx context.Context, args ...string) (map[string]any, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	ctx, cancel := context.WithTimeout(ctx, r.timeout)
	defer cancel()
	cmd := exec.CommandContext(ctx, r.cli, args...)
	cmd.Dir = r.workspace
	stdout := &limitedBuffer{remaining: maxCommandOutput}
	stderr := &limitedBuffer{remaining: maxCommandOutput}
	cmd.Stdout = stdout
	cmd.Stderr = stderr
	err := cmd.Run()
	if ctx.Err() != nil {
		return nil, fmt.Errorf("Colofon command timed out after %s", r.timeout)
	}
	if stdout.truncated || stderr.truncated {
		return nil, errors.New("Colofon command output exceeded 1 MiB")
	}
	var payload map[string]any
	if jsonErr := json.Unmarshal(stdout.Bytes(), &payload); jsonErr != nil {
		message := strings.TrimSpace(stderr.String())
		if message == "" {
			message = strings.TrimSpace(stdout.String())
		}
		if err != nil {
			return nil, fmt.Errorf("Colofon command failed: %s", message)
		}
		return nil, fmt.Errorf("decode Colofon JSON result: %w", jsonErr)
	}
	if err != nil {
		if ok, _ := payload["ok"].(bool); ok {
			return nil, errors.New("Colofon command failed without an error result")
		}
	}
	return payload, nil
}

func toolResult(payload map[string]any) *mcp.CallToolResult {
	ok, _ := payload["ok"].(bool)
	return &mcp.CallToolResult{IsError: !ok}
}

func (r *Runner) buildDocument(ctx context.Context, input DocumentInput) (*mcp.CallToolResult, map[string]any, error) {
	source, err := r.source(input.Source, ".md")
	if err != nil {
		return nil, nil, fmt.Errorf("invalid source: %w", err)
	}
	output, err := r.output(input.Output, source)
	if err != nil {
		return nil, nil, fmt.Errorf("invalid output: %w", err)
	}
	payload, err := r.command(ctx, "doc", source, "--root", r.workspace, "-o", output, "--json")
	return toolResult(payload), payload, err
}

func (r *Runner) buildBook(ctx context.Context, input BookInput) (*mcp.CallToolResult, map[string]any, error) {
	source, err := r.source(input.Source, ".yaml", ".yml")
	if err != nil {
		return nil, nil, fmt.Errorf("invalid source: %w", err)
	}
	output, err := r.output(input.Output, source)
	if err != nil {
		return nil, nil, fmt.Errorf("invalid output: %w", err)
	}
	payload, err := r.command(ctx, "book", source, "--root", r.workspace, "-o", output, "--json")
	return toolResult(payload), payload, err
}

func (r *Runner) lint(ctx context.Context, input LintInput) (*mcp.CallToolResult, map[string]any, error) {
	if len(input.Sources) == 0 {
		return nil, nil, errors.New("at least one source is required")
	}
	args := []string{"lint", "--json"}
	for _, path := range input.Sources {
		source, err := r.source(path, ".md")
		if err != nil {
			return nil, nil, fmt.Errorf("invalid source %q: %w", path, err)
		}
		args = append(args, source)
	}
	payload, err := r.command(ctx, args...)
	return toolResult(payload), payload, err
}

func (r *Runner) describe(ctx context.Context, _ DescribeInput) (*mcp.CallToolResult, map[string]any, error) {
	payload, err := r.command(ctx, "describe", "--json")
	return toolResult(payload), payload, err
}

func boolPointer(value bool) *bool { return &value }

// Server constructs the stdio MCP server with Colofon's core tools.
func Server(runner *Runner) *mcp.Server {
	server := mcp.NewServer(
		&mcp.Implementation{Name: "colofon", Version: Version},
		&mcp.ServerOptions{Instructions: instructions},
	)
	closed := boolPointer(false)
	mcp.AddTool(server, &mcp.Tool{
		Name:        "colofon_describe",
		Title:       "Describe Colofon Authoring",
		Description: "Return Colofon's current document schemas, book schema, versions, and enabled capabilities.",
		Annotations: &mcp.ToolAnnotations{ReadOnlyHint: true, OpenWorldHint: closed},
	}, func(ctx context.Context, _ *mcp.CallToolRequest, input DescribeInput) (*mcp.CallToolResult, map[string]any, error) {
		return runner.describe(ctx, input)
	})
	mcp.AddTool(server, &mcp.Tool{
		Name:        "colofon_lint",
		Title:       "Lint Colofon Markdown",
		Description: "Check workspace Markdown for accessibility, screenshot, and cross-reference problems without building a PDF.",
		Annotations: &mcp.ToolAnnotations{ReadOnlyHint: true, OpenWorldHint: closed},
	}, func(ctx context.Context, _ *mcp.CallToolRequest, input LintInput) (*mcp.CallToolResult, map[string]any, error) {
		return runner.lint(ctx, input)
	})
	mcp.AddTool(server, &mcp.Tool{
		Name:        "colofon_build_document",
		Title:       "Build a Colofon Document",
		Description: "Build one Markdown document to build/ and run Colofon's PDF/UA-1 and copy-safety gates.",
		Annotations: &mcp.ToolAnnotations{
			DestructiveHint: boolPointer(false), IdempotentHint: true, OpenWorldHint: closed,
		},
	}, func(ctx context.Context, _ *mcp.CallToolRequest, input DocumentInput) (*mcp.CallToolResult, map[string]any, error) {
		return runner.buildDocument(ctx, input)
	})
	mcp.AddTool(server, &mcp.Tool{
		Name:        "colofon_build_book",
		Title:       "Build a Colofon Book",
		Description: "Build one YAML/Markdown book to build/ and run Colofon's PDF/UA-1 and copy-safety gates.",
		Annotations: &mcp.ToolAnnotations{
			DestructiveHint: boolPointer(false), IdempotentHint: true, OpenWorldHint: closed,
		},
	}, func(ctx context.Context, _ *mcp.CallToolRequest, input BookInput) (*mcp.CallToolResult, map[string]any, error) {
		return runner.buildBook(ctx, input)
	})
	return server
}

var _ io.Writer = (*limitedBuffer)(nil)

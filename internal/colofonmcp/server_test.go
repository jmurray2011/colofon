package colofonmcp

import (
	"context"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func writeTestFile(t *testing.T, path, content string, mode os.FileMode) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(content), mode); err != nil {
		t.Fatal(err)
	}
}

func testRunner(t *testing.T) (*Runner, string) {
	t.Helper()
	workspace := t.TempDir()
	cli := filepath.Join(t.TempDir(), "colofon")
	writeTestFile(t, cli, "#!/bin/sh\nprintf '%s\\n' \"$@\" > \"$PWD/invocation\"\nprintf '{\"ok\":true}'\n", 0o755)
	runner, err := NewRunner(workspace, cli, time.Second)
	if err != nil {
		t.Fatal(err)
	}
	return runner, workspace
}

func TestVersionMatchesRepository(t *testing.T) {
	contents, err := os.ReadFile(filepath.Join("..", "..", "VERSION"))
	if err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(string(contents)) != Version {
		t.Fatalf("server version %q does not match VERSION", Version)
	}
}

func TestBuildDocumentUsesConfinedPaths(t *testing.T) {
	runner, workspace := testRunner(t)
	writeTestFile(t, filepath.Join(workspace, "source.md"), "---\ndoctype: report\ntitle: Test\n---\n", 0o644)
	result, payload, err := runner.buildDocument(
		context.Background(), DocumentInput{Source: "source.md"},
	)
	if err != nil {
		t.Fatal(err)
	}
	if result.IsError || payload["ok"] != true {
		t.Fatalf("unexpected result: %#v %#v", result, payload)
	}
	invocation, err := os.ReadFile(filepath.Join(workspace, "invocation"))
	if err != nil {
		t.Fatal(err)
	}
	got := string(invocation)
	for _, want := range []string{"doc\n", "source.md\n", "build/source.pdf\n", "--json\n"} {
		if !strings.Contains(got, want) {
			t.Errorf("invocation %q does not contain %q", got, want)
		}
	}
}

func TestRejectsSourceSymlinkEscape(t *testing.T) {
	runner, workspace := testRunner(t)
	outside := filepath.Join(t.TempDir(), "private.md")
	writeTestFile(t, outside, "private", 0o644)
	if err := os.Symlink(outside, filepath.Join(workspace, "source.md")); err != nil {
		t.Fatal(err)
	}
	_, _, err := runner.buildDocument(context.Background(), DocumentInput{Source: "source.md"})
	if err == nil || !strings.Contains(err.Error(), "outside") {
		t.Fatalf("expected symlink escape rejection, got %v", err)
	}
}

func TestRejectsOutputOutsideBuild(t *testing.T) {
	runner, workspace := testRunner(t)
	writeTestFile(t, filepath.Join(workspace, "source.md"), "test", 0o644)
	for _, output := range []string{"source.pdf", "../source.pdf", "/tmp/source.pdf"} {
		_, _, err := runner.buildDocument(
			context.Background(), DocumentInput{Source: "source.md", Output: output},
		)
		if err == nil {
			t.Errorf("output %q was accepted", output)
		}
	}
}

func TestRejectsBuildDirectorySymlinkEscape(t *testing.T) {
	runner, workspace := testRunner(t)
	writeTestFile(t, filepath.Join(workspace, "source.md"), "test", 0o644)
	if err := os.Symlink(t.TempDir(), filepath.Join(workspace, "build")); err != nil {
		t.Fatal(err)
	}
	_, _, err := runner.buildDocument(context.Background(), DocumentInput{Source: "source.md"})
	if err == nil || !strings.Contains(err.Error(), "symlink") {
		t.Fatalf("expected build symlink rejection, got %v", err)
	}
}

func TestRejectsNestedOutputSymlinkBeforeWritingOutside(t *testing.T) {
	runner, workspace := testRunner(t)
	writeTestFile(t, filepath.Join(workspace, "source.md"), "test", 0o644)
	outside := t.TempDir()
	if err := os.Mkdir(filepath.Join(workspace, "build"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(outside, filepath.Join(workspace, "build", "linked")); err != nil {
		t.Fatal(err)
	}
	_, _, err := runner.buildDocument(context.Background(), DocumentInput{
		Source: "source.md", Output: "build/linked/new/report.pdf",
	})
	if err == nil || !strings.Contains(err.Error(), "symlink") {
		t.Fatalf("expected nested symlink rejection, got %v", err)
	}
	if _, statErr := os.Stat(filepath.Join(outside, "new")); !os.IsNotExist(statErr) {
		t.Fatalf("server wrote outside workspace before rejecting path: %v", statErr)
	}
}

func TestCommandOutputIsBounded(t *testing.T) {
	buffer := &limitedBuffer{remaining: 4}
	written, err := buffer.Write([]byte("123456"))
	if err != nil || written != 6 {
		t.Fatalf("Write() = %d, %v", written, err)
	}
	if buffer.String() != "1234" || !buffer.truncated {
		t.Fatalf("buffer = %q, truncated = %v", buffer.String(), buffer.truncated)
	}
}

func TestServerPublishesOnlyCoreTools(t *testing.T) {
	runner, _ := testRunner(t)
	clientTransport, serverTransport := mcp.NewInMemoryTransports()
	serverSession, err := Server(runner).Connect(context.Background(), serverTransport, nil)
	if err != nil {
		t.Fatal(err)
	}
	defer serverSession.Close()
	client := mcp.NewClient(&mcp.Implementation{Name: "test", Version: "1"}, nil)
	clientSession, err := client.Connect(context.Background(), clientTransport, nil)
	if err != nil {
		t.Fatal(err)
	}
	defer clientSession.Close()
	listed, err := clientSession.ListTools(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	var names []string
	for _, tool := range listed.Tools {
		names = append(names, tool.Name)
	}
	sort.Strings(names)
	want := []string{"colofon_build_book", "colofon_build_document", "colofon_lint"}
	if strings.Join(names, ",") != strings.Join(want, ",") {
		t.Fatalf("tool names = %v, want %v", names, want)
	}
}

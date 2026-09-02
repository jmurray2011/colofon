// colofon-mcp exposes the core Colofon factory over local MCP stdio transport.
package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/jmurray2011/colofon/internal/colofonmcp"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func main() {
	workspace := flag.String("workspace", ".", "workspace directory exposed to Colofon")
	cli := flag.String("colofon", "colofon", "path to the Colofon CLI")
	timeout := flag.Duration("timeout", 10*time.Minute, "maximum duration of one tool call")
	stdio := flag.Bool("stdio", true, "serve MCP over stdin/stdout (the only supported transport)")
	flag.Parse()
	if !*stdio {
		fmt.Fprintln(os.Stderr, "colofon-mcp: only stdio transport is supported")
		os.Exit(2)
	}
	runner, err := colofonmcp.NewRunner(*workspace, *cli, *timeout)
	if err != nil {
		log.Fatal(err)
	}
	if err := colofonmcp.Server(runner).Run(context.Background(), &mcp.StdioTransport{}); err != nil {
		log.Fatal(err)
	}
}

package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var (
	version = "0.3.0-dev"
	commit  = "unknown"
)

func main() {
	root := &cobra.Command{
		Use:   "devflow",
		Short: "Local development platform for AO Cyber Systems",
		Long: `devflow manages your local multi-project development environment:
project registry, baseline services, *.test domains, secrets, toolchain,
dependency graph, supply chain, and Claude Code + MCP lifecycle.

See https://github.com/AO-Cyber-Systems/devflow-dev for the broader family
architecture and roadmap.`,
	}

	root.AddCommand(versionCmd())

	// Subsystem stubs — implemented in subsequent phases.
	root.AddCommand(stubCmd("project", "Project registry and lifecycle (Phase 2)"))
	root.AddCommand(stubCmd("baseline", "Shared baseline stack orchestration (Phase 2)"))
	root.AddCommand(stubCmd("domain", "*.test domains and local TLS (Phase 2)"))
	root.AddCommand(stubCmd("secrets", "Two-tier secrets management (Phase 2)"))
	root.AddCommand(stubCmd("tools", "Mise + Homebrew toolchain (Phase 3.5)"))
	root.AddCommand(stubCmd("deps", "Cross-project dependency graph (Phase 6)"))
	root.AddCommand(stubCmd("supply", "Supply chain review (Phase 7)"))
	root.AddCommand(stubCmd("mcp", "MCP server registry (Phase 4)"))
	root.AddCommand(stubCmd("claude", "Claude Code lifecycle (Phase 4)"))
	root.AddCommand(stubCmd("doctor", "Health checks across every subsystem"))
	root.AddCommand(stubCmd("daemon", "Run the gRPC daemon (Phase 3)"))

	if err := root.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func versionCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "version",
		Short: "Print devflow version",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Printf("devflow %s (%s)\n", version, commit)
		},
	}
}

func stubCmd(name, short string) *cobra.Command {
	return &cobra.Command{
		Use:   name,
		Short: short,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Fprintf(os.Stderr, "%s: not implemented yet — see ROADMAP in devflow-dev\n", name)
			os.Exit(2)
		},
	}
}

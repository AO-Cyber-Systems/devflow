import SwiftUI

struct ToolCheckView: View {
    @Environment(AppState.self) private var appState
    let template: Template?
    let toolCheck: ToolCheckResponse?

    @State private var installingToolIds: Set<String> = []

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Header
            VStack(alignment: .leading, spacing: 4) {
                Text("Tool Check")
                    .font(.title2)
                    .fontWeight(.semibold)

                Text("Make sure you have the required tools installed before creating your project.")
                    .font(.body)
                    .foregroundStyle(.secondary)
            }

            if let check = toolCheck {
                // Required tools
                if !check.required.isEmpty {
                    toolSection(
                        title: "Required Tools",
                        tools: check.required,
                        isRequired: true
                    )
                }

                // Recommended tools
                if !check.recommended.isEmpty {
                    toolSection(
                        title: "Recommended Tools",
                        tools: check.recommended,
                        isRequired: false
                    )
                }

                // Status summary
                Spacer()

                if check.allRequiredInstalled {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                        Text("All required tools are installed. You can proceed.")
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color.green.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                } else {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundStyle(.orange)
                        Text("Some required tools are missing. Please install them before continuing.")
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color.orange.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                }
            } else {
                ProgressView("Checking tools...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .padding(24)
    }

    private func toolSection(
        title: String,
        tools: [ToolCheckItem],
        isRequired: Bool
    ) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(title)
                    .font(.headline)
                if isRequired {
                    Text("Required")
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.red.opacity(0.2))
                        .foregroundStyle(.red)
                        .clipShape(Capsule())
                }
            }

            VStack(spacing: 0) {
                ForEach(tools) { tool in
                    toolRow(tool, isRequired: isRequired)
                    if tool.id != tools.last?.id {
                        Divider()
                    }
                }
            }
            .background(Color(nsColor: .controlBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }

    private func toolRow(_ tool: ToolCheckItem, isRequired: Bool) -> some View {
        HStack(spacing: 12) {
            // Status icon
            Image(systemName: tool.installed ? "checkmark.circle.fill" : "circle")
                .foregroundStyle(tool.installed ? .green : (isRequired ? .red : .secondary))
                .font(.title3)

            // Tool name
            VStack(alignment: .leading, spacing: 2) {
                Text(tool.name)
                    .font(.body)

                if let version = tool.version, tool.installed {
                    Text("v\(version)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else if !tool.installed {
                    Text("Not installed")
                        .font(.caption)
                        .foregroundStyle(isRequired ? .red : .secondary)
                }
            }

            Spacer()

            // Install button
            if !tool.installed {
                if installingToolIds.contains(tool.toolId) {
                    ProgressView()
                        .controlSize(.small)
                } else {
                    Button("Install") {
                        Task {
                            await installTool(tool.toolId)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.small)
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
    }

    private func installTool(_ toolId: String) async {
        installingToolIds.insert(toolId)
        defer { installingToolIds.remove(toolId) }

        await appState.installTool(toolId)

        // Refresh tool check
        if let template = template {
            _ = await appState.checkRequiredTools(template.id)
        }
    }
}

#Preview {
    ToolCheckView(
        template: Template(
            id: "nextjs-fullstack",
            name: "nextjs-fullstack",
            displayName: "Next.js Fullstack",
            description: "Next.js with TypeScript",
            requiredTools: ["nodejs", "git"],
            recommendedTools: ["docker"]
        ),
        toolCheck: ToolCheckResponse(
            allRequiredInstalled: false,
            required: [
                ToolCheckItem(
                    toolId: "nodejs",
                    name: "Node.js",
                    installed: true,
                    version: "20.10.0",
                    error: nil
                ),
                ToolCheckItem(
                    toolId: "git",
                    name: "Git",
                    installed: false,
                    version: nil,
                    error: nil
                )
            ],
            recommended: [
                ToolCheckItem(
                    toolId: "docker",
                    name: "Docker",
                    installed: true,
                    version: "24.0.0",
                    error: nil
                )
            ]
        )
    )
    .environment(AppState())
    .frame(width: 600, height: 500)
}

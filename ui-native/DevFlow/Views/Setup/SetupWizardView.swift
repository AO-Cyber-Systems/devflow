import SwiftUI

enum SetupWizardStep: Int, CaseIterable {
    case welcome
    case essentialTools
    case optionalTools
    case complete

    var title: String {
        switch self {
        case .welcome: return "Welcome"
        case .essentialTools: return "Essential Tools"
        case .optionalTools: return "Optional Tools"
        case .complete: return "Complete"
        }
    }
}

struct SetupWizardView: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    @State private var currentStep: SetupWizardStep = .welcome
    @State private var essentialTools: [ToolStatus] = []
    @State private var optionalTools: [ToolStatus] = []
    @State private var isLoading = false
    @State private var installingToolIds: Set<String> = []

    var body: some View {
        VStack(spacing: 0) {
            // Progress indicator
            HStack(spacing: 4) {
                ForEach(SetupWizardStep.allCases, id: \.self) { step in
                    RoundedRectangle(cornerRadius: 2)
                        .fill(step.rawValue <= currentStep.rawValue ? Color.accentColor : Color.secondary.opacity(0.3))
                        .frame(height: 4)
                }
            }
            .padding(.horizontal, 24)
            .padding(.top, 16)

            // Content
            Group {
                switch currentStep {
                case .welcome:
                    welcomeStep
                case .essentialTools:
                    essentialToolsStep
                case .optionalTools:
                    optionalToolsStep
                case .complete:
                    completeStep
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            // Navigation
            HStack {
                if currentStep != .welcome {
                    Button("Back") {
                        withAnimation {
                            currentStep = SetupWizardStep(rawValue: currentStep.rawValue - 1) ?? .welcome
                        }
                    }
                    .buttonStyle(.bordered)
                }

                Spacer()

                if currentStep == .complete {
                    Button("Get Started") {
                        Task {
                            await appState.markSetupCompleted()
                            dismiss()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                } else {
                    Button("Continue") {
                        withAnimation {
                            currentStep = SetupWizardStep(rawValue: currentStep.rawValue + 1) ?? .complete
                        }
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding(24)
        }
        .frame(width: 600, height: 500)
        .task {
            await loadTools()
        }
        .onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)) { _ in
            // Refresh tools when app regains focus (e.g., after Terminal install completes)
            Task { await loadTools() }
        }
        .accessibilityIdentifier("setupWizard")
    }

    // MARK: - Welcome Step

    private var welcomeStep: some View {
        VStack(spacing: 24) {
            Spacer()

            Image(systemName: "wrench.and.screwdriver.fill")
                .font(.system(size: 64))
                .foregroundStyle(.blue)

            Text("Welcome to DevFlow")
                .font(.largeTitle)
                .fontWeight(.bold)

            Text("Let's set up your development environment. We'll check for essential tools and help you install any that are missing.")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 400)

            Spacer()
        }
        .padding(24)
    }

    // MARK: - Essential Tools Step

    private var essentialToolsStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Essential Tools")
                .font(.title2)
                .fontWeight(.semibold)

            Text("These tools are required for most development workflows.")
                .font(.body)
                .foregroundStyle(.secondary)

            if isLoading {
                ProgressView("Checking tools...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    VStack(spacing: 0) {
                        ForEach(essentialTools) { tool in
                            ToolInstallRow(tool: tool) {
                                await installTool(tool.toolId)
                            }
                            if tool.id != essentialTools.last?.id {
                                Divider()
                            }
                        }
                    }
                }
                .background(Color(nsColor: .controlBackgroundColor))
                .clipShape(RoundedRectangle(cornerRadius: 8))

                HStack {
                    let installedCount = essentialTools.filter(\.isInstalled).count
                    Text("\(installedCount) of \(essentialTools.count) installed")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Spacer()

                    Button {
                        Task { await loadTools() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                    .buttonStyle(.bordered)
                    .help("Refresh tool status")

                    if essentialTools.contains(where: { !$0.isInstalled }) {
                        Button("Install All") {
                            Task {
                                await installAllMissing(essentialTools)
                            }
                        }
                        .buttonStyle(.bordered)
                        .disabled(!installingToolIds.isEmpty)
                    }
                }
            }
        }
        .padding(24)
    }

    // MARK: - Optional Tools Step

    private var optionalToolsStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Optional Tools")
                .font(.title2)
                .fontWeight(.semibold)

            Text("These tools are recommended but not required. You can install them later.")
                .font(.body)
                .foregroundStyle(.secondary)

            if isLoading {
                ProgressView("Checking tools...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    VStack(spacing: 0) {
                        ForEach(optionalTools) { tool in
                            ToolInstallRow(tool: tool) {
                                await installTool(tool.toolId)
                            }
                            if tool.id != optionalTools.last?.id {
                                Divider()
                            }
                        }
                    }
                }
                .background(Color(nsColor: .controlBackgroundColor))
                .clipShape(RoundedRectangle(cornerRadius: 8))

                HStack {
                    let installedCount = optionalTools.filter(\.isInstalled).count
                    Text("\(installedCount) of \(optionalTools.count) installed")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Spacer()

                    Button {
                        Task { await loadTools() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                    .buttonStyle(.bordered)
                    .help("Refresh tool status")
                }
            }
        }
        .padding(24)
    }

    // MARK: - Complete Step

    private var completeStep: some View {
        VStack(spacing: 24) {
            Spacer()

            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 64))
                .foregroundStyle(.green)

            Text("You're All Set!")
                .font(.largeTitle)
                .fontWeight(.bold)

            Text("Your development environment is ready. You can now create projects, manage infrastructure, and more.")
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: 400)

            // Summary
            VStack(alignment: .leading, spacing: 8) {
                let essentialInstalled = essentialTools.filter(\.isInstalled).count
                let optionalInstalled = optionalTools.filter(\.isInstalled).count

                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                    Text("\(essentialInstalled) of \(essentialTools.count) essential tools installed")
                }

                HStack {
                    Image(systemName: optionalInstalled > 0 ? "checkmark.circle.fill" : "circle")
                        .foregroundStyle(optionalInstalled > 0 ? .green : .secondary)
                    Text("\(optionalInstalled) of \(optionalTools.count) optional tools installed")
                }
            }
            .font(.callout)
            .padding()
            .background(Color(nsColor: .controlBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 8))

            Spacer()
        }
        .padding(24)
    }

    // MARK: - Actions

    private func loadTools() async {
        isLoading = true
        defer { isLoading = false }

        await appState.loadEssentialTools()
        await appState.loadRecommendedTools()

        essentialTools = appState.essentialTools
        optionalTools = appState.recommendedTools
    }

    private func installTool(_ toolId: String) async {
        installingToolIds.insert(toolId)
        defer { installingToolIds.remove(toolId) }

        await appState.installTool(toolId)
        await loadTools()
    }

    private func installAllMissing(_ tools: [ToolStatus]) async {
        let missingIds = tools.filter { !$0.isInstalled }.map(\.toolId)
        for id in missingIds {
            installingToolIds.insert(id)
        }

        await appState.installMultipleTools(missingIds)
        installingToolIds.removeAll()
        await loadTools()
    }
}

#Preview {
    SetupWizardView()
        .environment(AppState())
}

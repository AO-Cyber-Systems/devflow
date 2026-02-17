import SwiftUI

enum ProjectWizardStep: Int, CaseIterable, Identifiable {
    case selectTemplate
    case configure
    case toolCheck
    case create

    var id: Int { rawValue }

    var title: String {
        switch self {
        case .selectTemplate: return "Choose Template"
        case .configure: return "Configure"
        case .toolCheck: return "Tool Check"
        case .create: return "Create"
        }
    }

    var icon: String {
        switch self {
        case .selectTemplate: return "square.grid.2x2"
        case .configure: return "slider.horizontal.3"
        case .toolCheck: return "checkmark.shield"
        case .create: return "plus.circle"
        }
    }
}

struct NewProjectWizardView: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    @State private var currentStep: ProjectWizardStep = .selectTemplate
    @State private var selectedTemplate: Template?
    @State private var templateDetail: TemplateDetail?
    @State private var wizardValues: [String: String] = [:]
    @State private var currentWizardStepIndex = 0
    @State private var toolCheck: ToolCheckResponse?
    @State private var isCreating = false
    @State private var createResult: CreateProjectResponse?
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 0) {
            // Step indicator
            stepIndicator
                .padding(.horizontal, 24)
                .padding(.top, 16)

            Divider()
                .padding(.top, 16)

            // Content
            Group {
                switch currentStep {
                case .selectTemplate:
                    TemplateSelectionView(selectedTemplate: $selectedTemplate)

                case .configure:
                    if let detail = templateDetail {
                        WizardStepView(
                            templateDetail: detail,
                            currentStepIndex: $currentWizardStepIndex,
                            values: $wizardValues
                        )
                    } else {
                        ProgressView("Loading template...")
                    }

                case .toolCheck:
                    ToolCheckView(
                        template: selectedTemplate,
                        toolCheck: toolCheck
                    )

                case .create:
                    createStepView
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            Divider()

            // Navigation
            navigationButtons
                .padding(24)
        }
        .frame(width: 800, height: 600)
        .onChange(of: selectedTemplate) { _, newTemplate in
            if let template = newTemplate {
                Task {
                    await loadTemplateDetail(template.id)
                }
            }
        }
        .accessibilityIdentifier("newProjectWizard")
    }

    // MARK: - Step Indicator

    private var stepIndicator: some View {
        HStack(spacing: 0) {
            ForEach(ProjectWizardStep.allCases) { step in
                HStack(spacing: 8) {
                    ZStack {
                        Circle()
                            .fill(stepCircleColor(for: step))
                            .frame(width: 28, height: 28)

                        if step.rawValue < currentStep.rawValue {
                            Image(systemName: "checkmark")
                                .font(.caption.bold())
                                .foregroundStyle(.white)
                        } else {
                            Text("\(step.rawValue + 1)")
                                .font(.caption.bold())
                                .foregroundStyle(step == currentStep ? .white : .secondary)
                        }
                    }

                    Text(step.title)
                        .font(.caption)
                        .foregroundStyle(step == currentStep ? .primary : .secondary)
                }

                if step != ProjectWizardStep.allCases.last {
                    Rectangle()
                        .fill(step.rawValue < currentStep.rawValue ? Color.accentColor : Color.secondary.opacity(0.3))
                        .frame(height: 2)
                        .frame(maxWidth: .infinity)
                }
            }
        }
    }

    private func stepCircleColor(for step: ProjectWizardStep) -> Color {
        if step.rawValue < currentStep.rawValue {
            return .accentColor
        } else if step == currentStep {
            return .accentColor
        } else {
            return Color.secondary.opacity(0.3)
        }
    }

    // MARK: - Create Step

    private var createStepView: some View {
        VStack(spacing: 24) {
            if isCreating {
                ProgressView("Creating project...")
                    .progressViewStyle(.circular)
            } else if let result = createResult {
                if result.success {
                    createSuccessView(result)
                } else {
                    createErrorView(result.error ?? "Unknown error")
                }
            } else {
                createReadyView
            }
        }
        .padding(24)
    }

    private var createReadyView: some View {
        VStack(spacing: 24) {
            Image(systemName: "folder.badge.plus")
                .font(.system(size: 64))
                .foregroundStyle(.blue)

            Text("Ready to Create")
                .font(.title2)
                .fontWeight(.semibold)

            if let template = selectedTemplate {
                VStack(alignment: .leading, spacing: 12) {
                    infoRow("Template", template.displayName)
                    if let projectName = wizardValues["project_name"] {
                        infoRow("Project Name", projectName)
                    }
                    if let projectPath = wizardValues["project_path"] {
                        infoRow("Location", projectPath)
                    }
                }
                .padding()
                .background(Color(nsColor: .controlBackgroundColor))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
        }
    }

    private func infoRow(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label)
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .fontWeight(.medium)
        }
    }

    private func createSuccessView(_ result: CreateProjectResponse) -> some View {
        VStack(spacing: 24) {
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 64))
                .foregroundStyle(.green)

            Text("Project Created!")
                .font(.title2)
                .fontWeight(.semibold)

            if let path = result.path {
                Text(path)
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .textSelection(.enabled)
            }

            if let nextSteps = result.nextSteps, !nextSteps.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Next Steps")
                        .font(.headline)

                    ForEach(nextSteps, id: \.self) { step in
                        HStack {
                            Image(systemName: "arrow.right")
                                .foregroundStyle(.secondary)
                            Text(step)
                                .font(.system(.body, design: .monospaced))
                        }
                    }
                }
                .padding()
                .background(Color(nsColor: .controlBackgroundColor))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }

            HStack(spacing: 12) {
                if let path = result.path {
                    Button("Open in Finder") {
                        NSWorkspace.shared.selectFile(nil, inFileViewerRootedAtPath: path)
                    }
                    .buttonStyle(.bordered)

                    Button("Open in Terminal") {
                        let script = "tell application \"Terminal\" to do script \"cd '\(path)'\""
                        if let appleScript = NSAppleScript(source: script) {
                            appleScript.executeAndReturnError(nil)
                        }
                    }
                    .buttonStyle(.bordered)
                }
            }
        }
    }

    private func createErrorView(_ error: String) -> some View {
        VStack(spacing: 24) {
            Image(systemName: "xmark.circle.fill")
                .font(.system(size: 64))
                .foregroundStyle(.red)

            Text("Creation Failed")
                .font(.title2)
                .fontWeight(.semibold)

            Text(error)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Button("Try Again") {
                createResult = nil
            }
            .buttonStyle(.bordered)
        }
    }

    // MARK: - Navigation

    private var navigationButtons: some View {
        HStack {
            Button("Cancel") {
                dismiss()
            }
            .keyboardShortcut(.cancelAction)

            Spacer()

            if currentStep != .selectTemplate {
                Button("Back") {
                    goBack()
                }
                .buttonStyle(.bordered)
            }

            if currentStep == .create {
                if createResult?.success == true {
                    Button("Done") {
                        dismiss()
                    }
                    .buttonStyle(.borderedProminent)
                } else if !isCreating {
                    Button("Create Project") {
                        Task {
                            await createProject()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(createResult != nil)
                }
            } else {
                Button("Continue") {
                    goForward()
                }
                .buttonStyle(.borderedProminent)
                .disabled(!canContinue)
            }
        }
    }

    private var canContinue: Bool {
        switch currentStep {
        case .selectTemplate:
            return selectedTemplate != nil
        case .configure:
            return true // Validation handled in WizardStepView
        case .toolCheck:
            return toolCheck?.allRequiredInstalled ?? false
        case .create:
            return true
        }
    }

    // MARK: - Actions

    private func goBack() {
        withAnimation {
            if currentStep == .configure && currentWizardStepIndex > 0 {
                currentWizardStepIndex -= 1
            } else if let newStep = ProjectWizardStep(rawValue: currentStep.rawValue - 1) {
                currentStep = newStep
                if newStep == .configure, let detail = templateDetail {
                    currentWizardStepIndex = detail.wizardSteps.count - 1
                }
            }
        }
    }

    private func goForward() {
        withAnimation {
            if currentStep == .configure, let detail = templateDetail {
                if currentWizardStepIndex < detail.wizardSteps.count - 1 {
                    currentWizardStepIndex += 1
                    return
                }
            }

            if let newStep = ProjectWizardStep(rawValue: currentStep.rawValue + 1) {
                currentStep = newStep

                if newStep == .toolCheck {
                    Task {
                        await loadToolCheck()
                    }
                }
            }
        }
    }

    private func loadTemplateDetail(_ templateId: String) async {
        templateDetail = await appState.loadTemplateDetail(templateId)
        wizardValues = [:]
        currentWizardStepIndex = 0

        // Set defaults
        if let detail = templateDetail {
            for step in detail.wizardSteps {
                for field in step.fields {
                    if let defaultValue = field.defaultValue {
                        wizardValues[field.id] = defaultValue
                    }
                }
            }
        }
    }

    private func loadToolCheck() async {
        guard let template = selectedTemplate else { return }
        toolCheck = await appState.checkRequiredTools(template.id)
    }

    private func createProject() async {
        guard let template = selectedTemplate else { return }

        isCreating = true
        defer { isCreating = false }

        createResult = await appState.createProject(
            templateId: template.id,
            values: wizardValues
        )
    }
}

#Preview {
    NewProjectWizardView()
        .environment(AppState())
}

import SwiftUI

struct WizardStepView: View {
    let templateDetail: TemplateDetail
    @Binding var currentStepIndex: Int
    @Binding var values: [String: String]

    @State private var validationErrors: [String: String] = [:]

    private var currentStep: WizardStep? {
        guard currentStepIndex < templateDetail.wizardSteps.count else { return nil }
        return templateDetail.wizardSteps[currentStepIndex]
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Step header
            if let step = currentStep {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Step \(currentStepIndex + 1) of \(templateDetail.wizardSteps.count)")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Text(step.title)
                        .font(.title2)
                        .fontWeight(.semibold)

                    if let description = step.description {
                        Text(description)
                            .font(.body)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Divider()

            // Fields
            if let step = currentStep {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        ForEach(step.fields) { field in
                            if shouldShowField(field) {
                                WizardFieldView(
                                    field: field,
                                    value: binding(for: field.id),
                                    error: validationErrors[field.id]
                                )
                            }
                        }
                    }
                    .padding(.horizontal, 4)
                }
            }
        }
        .padding(24)
    }

    private func shouldShowField(_ field: WizardField) -> Bool {
        guard let showWhen = field.showWhen else { return true }

        for (fieldId, expectedValue) in showWhen {
            if values[fieldId] != expectedValue {
                return false
            }
        }
        return true
    }

    private func binding(for fieldId: String) -> Binding<String> {
        Binding(
            get: { values[fieldId] ?? "" },
            set: { values[fieldId] = $0 }
        )
    }
}

// MARK: - Wizard Field View

struct WizardFieldView: View {
    let field: WizardField
    @Binding var value: String
    let error: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Label
            HStack(spacing: 4) {
                Text(field.label)
                    .font(.headline)
                if field.required {
                    Text("*")
                        .foregroundStyle(.red)
                }
            }

            // Description
            if let description = field.description {
                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            // Input
            Group {
                switch field.type {
                case .text:
                    textField
                case .number:
                    numberField
                case .select:
                    selectField
                case .multiselect:
                    multiselectField
                case .checkbox:
                    checkboxField
                case .directory:
                    directoryField
                }
            }

            // Error
            if let error = error {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
    }

    // MARK: - Field Types

    private var textField: some View {
        TextField(field.placeholder ?? "", text: $value)
            .textFieldStyle(.roundedBorder)
    }

    private var numberField: some View {
        TextField(field.placeholder ?? "", text: $value)
            .textFieldStyle(.roundedBorder)
    }

    private var selectField: some View {
        Picker("", selection: $value) {
            Text("Select...").tag("")
            ForEach(field.options) { option in
                Text(option.label).tag(option.value)
            }
        }
        .labelsHidden()
        .pickerStyle(.menu)
    }

    private var multiselectField: some View {
        VStack(alignment: .leading, spacing: 8) {
            ForEach(field.options) { option in
                Toggle(isOn: toggleBinding(for: option.value)) {
                    VStack(alignment: .leading) {
                        Text(option.label)
                        if let description = option.description {
                            Text(description)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(nsColor: .controlBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private func toggleBinding(for optionValue: String) -> Binding<Bool> {
        Binding(
            get: {
                let selected = value.split(separator: ",").map(String.init)
                return selected.contains(optionValue)
            },
            set: { isSelected in
                var selected = value.split(separator: ",").map(String.init)
                if isSelected {
                    if !selected.contains(optionValue) {
                        selected.append(optionValue)
                    }
                } else {
                    selected.removeAll { $0 == optionValue }
                }
                value = selected.joined(separator: ",")
            }
        )
    }

    private var checkboxField: some View {
        Toggle(isOn: Binding(
            get: { value == "true" },
            set: { value = $0 ? "true" : "false" }
        )) {
            EmptyView()
        }
        .labelsHidden()
    }

    private var directoryField: some View {
        HStack {
            TextField(field.placeholder ?? "Select a directory...", text: $value)
                .textFieldStyle(.roundedBorder)

            Button("Browse...") {
                let panel = NSOpenPanel()
                panel.canChooseFiles = false
                panel.canChooseDirectories = true
                panel.allowsMultipleSelection = false
                panel.canCreateDirectories = true

                if panel.runModal() == .OK, let url = panel.url {
                    value = url.path
                }
            }
        }
    }
}

#Preview {
    WizardStepView(
        templateDetail: TemplateDetail(
            id: "test",
            name: "test",
            displayName: "Test Template",
            description: "A test template",
            category: .web,
            icon: nil,
            author: nil,
            version: "1.0.0",
            tags: [],
            source: .builtin,
            requiredTools: [],
            recommendedTools: [],
            wizardSteps: [
                WizardStep(
                    id: "basics",
                    title: "Project Basics",
                    description: "Configure basic project settings",
                    fields: [
                        WizardField(
                            id: "project_name",
                            type: .text,
                            label: "Project Name",
                            required: true,
                            placeholder: "my-project"
                        ),
                        WizardField(
                            id: "project_path",
                            type: .directory,
                            label: "Location",
                            required: true
                        ),
                        WizardField(
                            id: "database",
                            type: .select,
                            label: "Database",
                            options: [
                                WizardFieldOption(value: "postgres", label: "PostgreSQL"),
                                WizardFieldOption(value: "mysql", label: "MySQL"),
                                WizardFieldOption(value: "none", label: "None")
                            ]
                        )
                    ]
                )
            ],
            files: [],
            hooks: []
        ),
        currentStepIndex: .constant(0),
        values: .constant([:])
    )
    .frame(width: 500, height: 400)
}

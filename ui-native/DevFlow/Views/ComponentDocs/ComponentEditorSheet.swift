import SwiftUI

struct ComponentEditorSheet: View {
    let projectPath: String
    let existingComponent: ComponentDoc?

    @Environment(\.dismiss) private var dismiss
    @Environment(AppState.self) private var appState

    @State private var name = ""
    @State private var selectedCategory = "form"
    @State private var description = ""
    @State private var aiGuidance = ""
    @State private var tags = ""
    @State private var accessibility: [String] = []
    @State private var newAccessibilityNote = ""

    @State private var isSaving = false

    var isEditing: Bool {
        existingComponent != nil
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Basic Info") {
                    if !isEditing {
                        TextField("Component Name", text: $name)
                    } else {
                        HStack {
                            Text("Name")
                            Spacer()
                            Text(existingComponent!.name)
                                .foregroundStyle(.secondary)
                        }
                    }

                    Picker("Category", selection: $selectedCategory) {
                        ForEach(appState.allComponentCategories) { category in
                            Label(category.name, systemImage: category.icon)
                                .tag(category.categoryId)
                        }
                    }

                    TextField("Description", text: $description, axis: .vertical)
                        .lineLimit(2...4)
                }

                Section("AI Guidance") {
                    Text("Add guidance to help AI tools use this component correctly.")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    TextEditor(text: $aiGuidance)
                        .font(.system(.body, design: .monospaced))
                        .frame(minHeight: 100)
                }

                Section("Accessibility Notes") {
                    ForEach(accessibility.indices, id: \.self) { index in
                        HStack {
                            Text(accessibility[index])
                            Spacer()
                            Button {
                                accessibility.remove(at: index)
                            } label: {
                                Image(systemName: "minus.circle")
                                    .foregroundStyle(.red)
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    HStack {
                        TextField("Add accessibility note", text: $newAccessibilityNote)
                        Button {
                            if !newAccessibilityNote.isEmpty {
                                accessibility.append(newAccessibilityNote)
                                newAccessibilityNote = ""
                            }
                        } label: {
                            Image(systemName: "plus.circle")
                        }
                        .buttonStyle(.plain)
                        .disabled(newAccessibilityNote.isEmpty)
                    }
                }

                Section("Tags") {
                    TextField("Comma-separated tags", text: $tags)
                }
            }
            .formStyle(.grouped)
            .navigationTitle(isEditing ? "Edit Component" : "Add Component")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task {
                            await save()
                        }
                    }
                    .disabled(isSaving || !isValid)
                }
            }
            .onAppear {
                if let component = existingComponent {
                    name = component.name
                    selectedCategory = component.category
                    description = component.description
                    aiGuidance = component.aiGuidance ?? ""
                    tags = component.tags.joined(separator: ", ")
                    accessibility = component.accessibility
                }
            }
        }
        .frame(minWidth: 500, minHeight: 500)
        .task {
            if appState.allComponentCategories.isEmpty {
                await appState.loadAllComponentCategories()
            }
        }
    }

    private var isValid: Bool {
        !name.isEmpty && !description.isEmpty
    }

    private func save() async {
        isSaving = true
        defer { isSaving = false }

        let tagList = tags.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }

        if isEditing {
            _ = await appState.updateComponent(
                projectPath: projectPath,
                name: name,
                category: selectedCategory,
                description: description,
                aiGuidance: aiGuidance.isEmpty ? nil : aiGuidance,
                accessibility: accessibility,
                tags: tagList
            )
        } else {
            _ = await appState.createComponent(
                projectPath: projectPath,
                name: name,
                category: selectedCategory,
                description: description,
                aiGuidance: aiGuidance.isEmpty ? nil : aiGuidance,
                accessibility: accessibility,
                tags: tagList
            )
        }

        dismiss()
    }
}

#Preview {
    ComponentEditorSheet(projectPath: "/path/to/project", existingComponent: nil)
        .environment(AppState())
}

import SwiftUI

struct ComponentDetailView: View {
    let component: ComponentDoc
    let projectPath: String

    @Environment(\.dismiss) private var dismiss
    @Environment(AppState.self) private var appState

    @State private var showEditorSheet = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header
                    HStack {
                        Image(systemName: component.categoryIcon)
                            .font(.title)
                            .foregroundStyle(.blue)
                            .frame(width: 50, height: 50)
                            .background(Color.blue.opacity(0.15))
                            .cornerRadius(10)

                        VStack(alignment: .leading) {
                            Text(component.name)
                                .font(.title2)
                                .fontWeight(.bold)

                            Label(component.categoryDisplay, systemImage: component.categoryIcon)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }

                        Spacer()

                        Button("Edit") {
                            showEditorSheet = true
                        }
                        .buttonStyle(.bordered)
                    }

                    Text(component.description)
                        .foregroundStyle(.secondary)

                    if !component.tags.isEmpty {
                        HStack {
                            ForEach(component.tags, id: \.self) { tag in
                                Text(tag)
                                    .font(.caption)
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(Color.secondary.opacity(0.15))
                                    .cornerRadius(4)
                            }
                        }
                    }

                    Divider()

                    // AI Guidance
                    if let aiGuidance = component.aiGuidance, !aiGuidance.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Label("AI Guidance", systemImage: "brain")
                                .font(.headline)

                            Text(aiGuidance)
                                .font(.system(.body, design: .monospaced))
                                .padding()
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .background(Color.purple.opacity(0.1))
                                .cornerRadius(8)
                        }

                        Divider()
                    }

                    // Props
                    if !component.props.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Label("Props", systemImage: "slider.horizontal.3")
                                .font(.headline)

                            ForEach(component.props) { prop in
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text(prop.name)
                                            .font(.system(.body, design: .monospaced))
                                            .fontWeight(.semibold)

                                        Text(prop.type)
                                            .font(.caption)
                                            .padding(.horizontal, 6)
                                            .padding(.vertical, 2)
                                            .background(Color.blue.opacity(0.15))
                                            .cornerRadius(4)

                                        if prop.required {
                                            Text("required")
                                                .font(.caption)
                                                .foregroundStyle(.red)
                                        }

                                        Spacer()

                                        if let defaultValue = prop.defaultValue {
                                            Text("default: \(defaultValue)")
                                                .font(.caption)
                                                .foregroundStyle(.secondary)
                                        }
                                    }

                                    if !prop.description.isEmpty {
                                        Text(prop.description)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }

                                    if !prop.options.isEmpty {
                                        HStack {
                                            Text("Options:")
                                                .font(.caption)
                                                .foregroundStyle(.secondary)
                                            Text(prop.options.joined(separator: " | "))
                                                .font(.system(.caption, design: .monospaced))
                                        }
                                    }
                                }
                                .padding()
                                .background(Color.secondary.opacity(0.05))
                                .cornerRadius(6)
                            }
                        }

                        Divider()
                    }

                    // Events
                    if !component.events.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Label("Events", systemImage: "bolt")
                                .font(.headline)

                            ForEach(component.events) { event in
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text("@\(event.name)")
                                            .font(.system(.body, design: .monospaced))
                                            .fontWeight(.semibold)

                                        if let payloadType = event.payloadType {
                                            Text(payloadType)
                                                .font(.caption)
                                                .padding(.horizontal, 6)
                                                .padding(.vertical, 2)
                                                .background(Color.orange.opacity(0.15))
                                                .cornerRadius(4)
                                        }
                                    }

                                    if !event.description.isEmpty {
                                        Text(event.description)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                .padding()
                                .background(Color.secondary.opacity(0.05))
                                .cornerRadius(6)
                            }
                        }

                        Divider()
                    }

                    // Slots
                    if !component.slots.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Label("Slots", systemImage: "square.dashed")
                                .font(.headline)

                            ForEach(component.slots) { slot in
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(slot.name)
                                        .font(.system(.body, design: .monospaced))
                                        .fontWeight(.semibold)

                                    if !slot.description.isEmpty {
                                        Text(slot.description)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                .padding()
                                .background(Color.secondary.opacity(0.05))
                                .cornerRadius(6)
                            }
                        }

                        Divider()
                    }

                    // Examples
                    if !component.examples.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Label("Examples", systemImage: "doc.text")
                                .font(.headline)

                            ForEach(component.examples) { example in
                                VStack(alignment: .leading, spacing: 8) {
                                    Text(example.title)
                                        .font(.subheadline)
                                        .fontWeight(.semibold)

                                    if !example.description.isEmpty {
                                        Text(example.description)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }

                                    Text(example.code)
                                        .font(.system(.caption, design: .monospaced))
                                        .padding()
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                        .background(Color.secondary.opacity(0.1))
                                        .cornerRadius(6)
                                }
                                .padding()
                                .background(Color.green.opacity(0.05))
                                .cornerRadius(8)
                            }
                        }

                        Divider()
                    }

                    // Accessibility
                    if !component.accessibility.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Label("Accessibility", systemImage: "accessibility")
                                .font(.headline)

                            ForEach(component.accessibility, id: \.self) { note in
                                HStack(alignment: .top) {
                                    Image(systemName: "checkmark.circle")
                                        .foregroundStyle(.green)
                                    Text(note)
                                }
                                .font(.caption)
                            }
                        }

                        Divider()
                    }

                    // Metadata
                    VStack(alignment: .leading, spacing: 4) {
                        if let sourceFile = component.sourceFile {
                            HStack {
                                Text("Source:")
                                    .foregroundStyle(.secondary)
                                Text(sourceFile)
                                    .font(.system(.caption, design: .monospaced))
                            }
                        }

                        HStack {
                            Text("Updated:")
                                .foregroundStyle(.secondary)
                            Text(component.updatedAt)
                        }
                    }
                    .font(.caption)
                }
                .padding()
            }
            .navigationTitle(component.name)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") {
                        dismiss()
                    }
                }
            }
        }
        .frame(minWidth: 600, minHeight: 600)
        .sheet(isPresented: $showEditorSheet) {
            ComponentEditorSheet(projectPath: projectPath, existingComponent: component)
        }
    }
}

#Preview {
    ComponentDetailView(
        component: ComponentDoc(
            name: "Button",
            category: "form",
            categoryDisplay: "Form Controls",
            categoryIcon: "rectangle.and.pencil.and.ellipsis",
            description: "Primary button component for actions",
            props: [
                PropDefinition(name: "variant", type: "string", description: "Button style variant", defaultValue: "primary", required: false, options: ["primary", "secondary", "danger"]),
                PropDefinition(name: "loading", type: "boolean", description: "Show loading state", defaultValue: "false", required: false, options: []),
            ],
            slots: [
                SlotDefinition(name: "default", description: "Button content", defaultContent: nil),
            ],
            events: [
                EventDefinition(name: "click", description: "Emitted when clicked", payloadType: "MouseEvent", payloadDescription: nil),
            ],
            examples: [
                ComponentExample(title: "Primary Button", code: "<Button variant=\"primary\">Save</Button>", description: "Basic primary button", language: "html"),
            ],
            aiGuidance: "Use Button for all clickable actions. Prefer variant=\"primary\" for CTAs.",
            accessibility: ["Always include visible label text", "Use aria-disabled for loading state"],
            tags: ["form", "interactive"],
            sourceFile: "src/components/Button.vue",
            createdAt: "2024-01-30T12:00:00",
            updatedAt: "2024-01-30T12:00:00"
        ),
        projectPath: "/path/to/project"
    )
    .environment(AppState())
}

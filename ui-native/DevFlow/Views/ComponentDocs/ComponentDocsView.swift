import SwiftUI

struct ComponentDocsView: View {
    @Environment(AppState.self) private var appState
    let projectPath: String

    @State private var selectedComponent: ComponentDoc?
    @State private var showEditorSheet = false
    @State private var showScanAlert = false
    @State private var scannedComponents: [ComponentDoc] = []

    var body: some View {
        VStack(spacing: 0) {
            // Search and filter bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("Search components...", text: Binding(
                    get: { appState.componentSearchQuery },
                    set: { appState.componentSearchQuery = $0 }
                ))
                .textFieldStyle(.plain)
                .onSubmit {
                    Task {
                        await appState.loadComponents(projectPath: projectPath)
                    }
                }

                if !appState.componentSearchQuery.isEmpty {
                    Button {
                        appState.componentSearchQuery = ""
                        Task {
                            await appState.loadComponents(projectPath: projectPath)
                        }
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }

                Divider()
                    .frame(height: 20)
                    .padding(.horizontal, 8)

                // Category filter
                Picker("Category", selection: Binding(
                    get: { appState.selectedComponentCategory ?? "all" },
                    set: {
                        appState.selectedComponentCategory = $0 == "all" ? nil : $0
                        Task {
                            await appState.loadComponents(projectPath: projectPath)
                        }
                    }
                )) {
                    Text("All Categories").tag("all")
                    ForEach(appState.componentCategories) { category in
                        Label(category.name, systemImage: category.icon)
                            .tag(category.categoryId)
                    }
                }
                .pickerStyle(.menu)
                .frame(width: 150)

                Button {
                    Task {
                        scannedComponents = await appState.scanComponents(projectPath: projectPath, save: false)
                        showScanAlert = true
                    }
                } label: {
                    Label("Scan", systemImage: "magnifyingglass")
                }
                .buttonStyle(.bordered)
                .disabled(appState.isScanningComponents)

                Button {
                    showEditorSheet = true
                } label: {
                    Label("Add", systemImage: "plus")
                }
                .buttonStyle(.borderedProminent)
            }
            .padding()

            Divider()

            // Main content
            if appState.isLoadingComponents && appState.components.isEmpty {
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.5)
                    Text("Loading components...")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if appState.isScanningComponents {
                VStack(spacing: 16) {
                    ProgressView()
                        .scaleEffect(1.5)
                    Text("Scanning project for components...")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if appState.components.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "square.stack.3d.up")
                        .font(.system(size: 48))
                        .foregroundStyle(.secondary)
                    Text("No component documentation yet")
                        .font(.title2)
                    Text("Scan your project to auto-detect components, or add them manually")
                        .foregroundStyle(.secondary)

                    HStack(spacing: 12) {
                        Button("Scan Project") {
                            Task {
                                scannedComponents = await appState.scanComponents(projectPath: projectPath, save: false)
                                showScanAlert = true
                            }
                        }
                        .buttonStyle(.bordered)

                        Button("Add Manually") {
                            showEditorSheet = true
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                List(selection: $selectedComponent) {
                    ForEach(appState.components) { component in
                        ComponentRowView(component: component)
                            .tag(component)
                            .contextMenu {
                                Button("Delete", role: .destructive) {
                                    Task {
                                        await appState.deleteComponent(component.name, projectPath: projectPath)
                                    }
                                }
                            }
                    }
                }
                .listStyle(.inset)
            }
        }
        .sheet(isPresented: $showEditorSheet) {
            ComponentEditorSheet(projectPath: projectPath, existingComponent: nil)
        }
        .sheet(item: $selectedComponent) { component in
            ComponentDetailView(component: component, projectPath: projectPath)
        }
        .alert("Components Found", isPresented: $showScanAlert) {
            Button("Save All") {
                Task {
                    _ = await appState.scanComponents(projectPath: projectPath, save: true)
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Found \(scannedComponents.count) components in your project. Save them as documentation?")
        }
        .task {
            if appState.components.isEmpty {
                await appState.loadAllComponentCategories()
                await appState.loadComponents(projectPath: projectPath)
                await appState.loadComponentCategories(projectPath: projectPath)
            }
        }
    }
}

struct ComponentRowView: View {
    let component: ComponentDoc

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: component.categoryIcon)
                .font(.title2)
                .foregroundStyle(.blue)
                .frame(width: 32)

            VStack(alignment: .leading, spacing: 2) {
                Text(component.name)
                    .font(.headline)

                HStack(spacing: 8) {
                    Text(component.categoryDisplay)
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.blue.opacity(0.15))
                        .cornerRadius(4)

                    Text("\(component.props.count) props")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    if !component.events.isEmpty {
                        Text("\(component.events.count) events")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                if !component.description.isEmpty {
                    Text(component.description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }

            Spacer()

            if component.aiGuidance != nil {
                Image(systemName: "brain")
                    .foregroundStyle(.purple)
                    .help("Has AI guidance")
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    ComponentDocsView(projectPath: "/path/to/project")
        .environment(AppState())
        .frame(width: 600, height: 400)
}

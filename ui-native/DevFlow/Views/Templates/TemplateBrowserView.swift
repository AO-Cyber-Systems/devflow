import SwiftUI

struct TemplateBrowserView: View {
    @Environment(AppState.self) private var appState

    @State private var searchText = ""
    @State private var selectedCategory: TemplateCategory?
    @State private var selectedTemplate: Template?
    @State private var showImportSheet = false
    @State private var showNewProjectWizard = false

    var filteredTemplates: [Template] {
        appState.templates.filter { template in
            // Category filter
            if let category = selectedCategory, template.category != category {
                return false
            }

            // Search filter
            if !searchText.isEmpty {
                let searchLower = searchText.lowercased()
                let nameMatch = template.name.lowercased().contains(searchLower)
                let displayMatch = template.displayName.lowercased().contains(searchLower)
                let descMatch = template.description.lowercased().contains(searchLower)
                let tagMatch = template.tags.contains { $0.lowercased().contains(searchLower) }

                if !nameMatch && !displayMatch && !descMatch && !tagMatch {
                    return false
                }
            }

            return true
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Category filter bar
            categoryFilterBar
                .padding(.horizontal)
                .padding(.vertical, 8)
                .background(Color(nsColor: .windowBackgroundColor))

            Divider()

            // Main content
            mainContent
        }
        .navigationTitle("Templates")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    showNewProjectWizard = true
                } label: {
                    Label("New Project", systemImage: "plus")
                }
            }

            ToolbarItem {
                Button {
                    showImportSheet = true
                } label: {
                    Label("Import", systemImage: "square.and.arrow.down")
                }
            }

            ToolbarItem {
                Button {
                    Task {
                        await appState.loadTemplates()
                    }
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                }
            }
        }
        .sheet(isPresented: $showImportSheet) {
            ImportTemplateSheet()
        }
        .sheet(isPresented: $showNewProjectWizard) {
            NewProjectWizardView()
        }
        .task {
            if appState.templates.isEmpty {
                await appState.loadTemplates()
            }
        }
        .accessibilityIdentifier("templateBrowser")
    }

    // MARK: - Category Filter Bar

    private var categoryFilterBar: some View {
        HStack(spacing: 12) {
            // Search field
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("Search templates...", text: $searchText)
                    .textFieldStyle(.plain)
            }
            .padding(8)
            .background(Color(nsColor: .controlBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 6))
            .frame(maxWidth: 250)

            Divider()
                .frame(height: 20)

            // Category pills
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    // All
                    CategoryPill(
                        title: "All",
                        icon: "square.grid.2x2",
                        count: appState.templates.count,
                        isSelected: selectedCategory == nil
                    ) {
                        selectedCategory = nil
                    }

                    // Each category with templates
                    ForEach(TemplateCategory.allCases, id: \.self) { category in
                        let count = appState.templates.filter { $0.category == category }.count
                        if count > 0 {
                            CategoryPill(
                                title: category.displayName,
                                icon: category.icon,
                                count: count,
                                isSelected: selectedCategory == category
                            ) {
                                selectedCategory = category
                            }
                        }
                    }
                }
            }

            Spacer()
        }
    }

    // MARK: - Main Content

    private var mainContent: some View {
        Group {
            if appState.isLoadingTemplates {
                ProgressView("Loading templates...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if filteredTemplates.isEmpty {
                emptyState
            } else {
                templateList
            }
        }
    }

    private var templateList: some View {
        ScrollView {
            LazyVGrid(
                columns: [
                    GridItem(.adaptive(minimum: 280, maximum: 350), spacing: 16)
                ],
                spacing: 16
            ) {
                ForEach(filteredTemplates) { template in
                    TemplateBrowserCard(
                        template: template,
                        isSelected: selectedTemplate?.id == template.id,
                        onSelect: {
                            selectedTemplate = template
                        },
                        onUse: {
                            showNewProjectWizard = true
                        },
                        onDelete: template.source != .builtin ? {
                            Task {
                                await appState.removeTemplate(template.id)
                            }
                        } : nil
                    )
                }
            }
            .padding()
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "doc.questionmark")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)

            Text("No Templates Found")
                .font(.title2)
                .fontWeight(.semibold)

            Text("Try adjusting your search or import a new template.")
                .font(.body)
                .foregroundStyle(.secondary)

            Button {
                showImportSheet = true
            } label: {
                Label("Import Template", systemImage: "square.and.arrow.down")
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Template Browser Card

struct TemplateBrowserCard: View {
    let template: Template
    let isSelected: Bool
    let onSelect: () -> Void
    let onUse: () -> Void
    let onDelete: (() -> Void)?

    @State private var isHovering = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header
            HStack(alignment: .top) {
                // Icon
                ZStack {
                    RoundedRectangle(cornerRadius: 8)
                        .fill(categoryColor.opacity(0.2))
                        .frame(width: 48, height: 48)

                    Image(systemName: template.category.icon)
                        .font(.title2)
                        .foregroundStyle(categoryColor)
                }

                Spacer()

                // Actions menu
                Menu {
                    Button {
                        onUse()
                    } label: {
                        Label("Use Template", systemImage: "plus.circle")
                    }

                    if let onDelete = onDelete {
                        Divider()
                        Button(role: .destructive) {
                            onDelete()
                        } label: {
                            Label("Delete", systemImage: "trash")
                        }
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .font(.title3)
                        .foregroundStyle(.secondary)
                }
                .menuStyle(.borderlessButton)
                .frame(width: 24, height: 24)
            }

            // Title & Source
            HStack {
                Text(template.displayName)
                    .font(.headline)
                    .lineLimit(1)

                if template.source != .builtin {
                    Text(template.source.displayName)
                        .font(.caption2)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.secondary.opacity(0.2))
                        .clipShape(Capsule())
                }
            }

            // Description
            Text(template.description)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(2)
                .frame(maxWidth: .infinity, alignment: .leading)

            // Meta info
            HStack(spacing: 12) {
                if let author = template.author {
                    Label(author, systemImage: "person")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Label(template.version, systemImage: "tag")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            // Tags
            if !template.tags.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 4) {
                        ForEach(template.tags, id: \.self) { tag in
                            Text(tag)
                                .font(.caption2)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.secondary.opacity(0.15))
                                .clipShape(Capsule())
                        }
                    }
                }
            }

            // Use button
            Button {
                onUse()
            } label: {
                Text("Use Template")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.small)
        }
        .padding()
        .background(Color(nsColor: .controlBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isSelected ? Color.accentColor : Color.clear, lineWidth: 2)
        )
        .shadow(color: .black.opacity(isHovering ? 0.15 : 0.05), radius: isHovering ? 8 : 4)
        .scaleEffect(isHovering ? 1.02 : 1.0)
        .animation(.easeInOut(duration: 0.15), value: isHovering)
        .onHover { hovering in
            isHovering = hovering
        }
        .onTapGesture {
            onSelect()
        }
    }

    private var categoryColor: Color {
        switch template.category {
        case .web: return .blue
        case .mobile: return .green
        case .desktop: return .purple
        case .fullstack: return .orange
        case .api: return .red
        case .library: return .teal
        case .other: return .gray
        }
    }
}

// MARK: - Category Pill

struct CategoryPill: View {
    let title: String
    let icon: String
    let count: Int
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.caption)
                Text(title)
                    .font(.caption)
                Text("\(count)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(isSelected ? Color.accentColor : Color(nsColor: .controlBackgroundColor))
            .foregroundStyle(isSelected ? .white : .primary)
            .clipShape(Capsule())
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    TemplateBrowserView()
        .environment(AppState())
        .frame(width: 900, height: 600)
}

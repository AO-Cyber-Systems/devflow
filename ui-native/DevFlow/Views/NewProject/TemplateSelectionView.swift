import SwiftUI

struct TemplateSelectionView: View {
    @Environment(AppState.self) private var appState
    @Binding var selectedTemplate: Template?

    @State private var searchText = ""
    @State private var selectedCategory: TemplateCategory?
    @State private var isLoading = false

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
        HSplitView {
            // Category sidebar
            categorySidebar
                .frame(width: 180)

            // Template grid
            templateGrid
        }
        .task {
            if appState.templates.isEmpty {
                await appState.loadTemplates()
            }
        }
    }

    // MARK: - Category Sidebar

    private var categorySidebar: some View {
        VStack(alignment: .leading, spacing: 0) {
            // All templates
            Button {
                selectedCategory = nil
            } label: {
                HStack {
                    Image(systemName: "square.grid.2x2")
                    Text("All Templates")
                    Spacer()
                    Text("\(appState.templates.count)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(selectedCategory == nil ? Color.accentColor.opacity(0.2) : Color.clear)
                .clipShape(RoundedRectangle(cornerRadius: 6))
            }
            .buttonStyle(.plain)

            Divider()
                .padding(.vertical, 8)

            // Categories
            ForEach(TemplateCategory.allCases, id: \.self) { category in
                let count = appState.templates.filter { $0.category == category }.count
                if count > 0 {
                    Button {
                        selectedCategory = category
                    } label: {
                        HStack {
                            Image(systemName: category.icon)
                            Text(category.displayName)
                            Spacer()
                            Text("\(count)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(selectedCategory == category ? Color.accentColor.opacity(0.2) : Color.clear)
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                    }
                    .buttonStyle(.plain)
                }
            }

            Spacer()
        }
        .padding(12)
        .background(Color(nsColor: .controlBackgroundColor))
    }

    // MARK: - Template Grid

    private var templateGrid: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("Search templates...", text: $searchText)
                    .textFieldStyle(.plain)
                if !searchText.isEmpty {
                    Button {
                        searchText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(8)
            .background(Color(nsColor: .controlBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .padding()

            // Grid
            if appState.isLoadingTemplates {
                ProgressView("Loading templates...")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if filteredTemplates.isEmpty {
                emptyState
            } else {
                ScrollView {
                    LazyVGrid(
                        columns: [
                            GridItem(.adaptive(minimum: 200, maximum: 280), spacing: 16)
                        ],
                        spacing: 16
                    ) {
                        ForEach(filteredTemplates) { template in
                            TemplateCard(
                                template: template,
                                isSelected: selectedTemplate?.id == template.id
                            ) {
                                selectedTemplate = template
                            }
                        }
                    }
                    .padding()
                }
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "doc.questionmark")
                .font(.largeTitle)
                .foregroundStyle(.secondary)
            Text("No templates found")
                .font(.headline)
            Text("Try adjusting your search or category filter")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Template Card

struct TemplateCard: View {
    let template: Template
    let isSelected: Bool
    let onSelect: () -> Void

    var body: some View {
        Button(action: onSelect) {
            VStack(alignment: .leading, spacing: 12) {
                // Header
                HStack {
                    // Icon
                    ZStack {
                        RoundedRectangle(cornerRadius: 8)
                            .fill(categoryColor.opacity(0.2))
                            .frame(width: 40, height: 40)

                        Image(systemName: template.category.icon)
                            .foregroundStyle(categoryColor)
                    }

                    Spacer()

                    // Source badge
                    if template.source != .builtin {
                        Text(template.source.displayName)
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.secondary.opacity(0.2))
                            .clipShape(Capsule())
                    }
                }

                // Title
                Text(template.displayName)
                    .font(.headline)
                    .lineLimit(1)

                // Description
                Text(template.description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)

                Spacer(minLength: 0)

                // Tags
                if !template.tags.isEmpty {
                    HStack(spacing: 4) {
                        ForEach(template.tags.prefix(3), id: \.self) { tag in
                            Text(tag)
                                .font(.caption2)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.secondary.opacity(0.15))
                                .clipShape(Capsule())
                        }
                        if template.tags.count > 3 {
                            Text("+\(template.tags.count - 3)")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .padding()
            .frame(height: 180)
            .background(Color(nsColor: .controlBackgroundColor))
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? Color.accentColor : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("templateCard_\(template.id)")
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

#Preview {
    TemplateSelectionView(selectedTemplate: .constant(nil))
        .environment(AppState())
        .frame(width: 700, height: 500)
}

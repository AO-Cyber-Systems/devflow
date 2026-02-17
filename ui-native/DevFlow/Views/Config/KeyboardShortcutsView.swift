import SwiftUI

/// A keyboard shortcut entry for display.
struct KeyboardShortcutEntry: Identifiable {
    let id = UUID()
    let shortcut: String
    let description: String
    let category: ShortcutCategory
}

/// Categories for organizing keyboard shortcuts.
enum ShortcutCategory: String, CaseIterable {
    case navigation = "Navigation"
    case actions = "Actions"
    case general = "General"
}

/// View displaying all available keyboard shortcuts.
struct KeyboardShortcutsView: View {
    @State private var searchText = ""
    @State private var selectedCategory: ShortcutCategory?

    private let shortcuts: [KeyboardShortcutEntry] = [
        // Navigation
        KeyboardShortcutEntry(shortcut: "Cmd+1", description: "Go to Dashboard", category: .navigation),
        KeyboardShortcutEntry(shortcut: "Cmd+2", description: "Go to Infrastructure", category: .navigation),
        KeyboardShortcutEntry(shortcut: "Cmd+3", description: "Go to Projects", category: .navigation),
        KeyboardShortcutEntry(shortcut: "Cmd+4", description: "Go to Databases", category: .navigation),
        KeyboardShortcutEntry(shortcut: "Cmd+5", description: "Go to Secrets", category: .navigation),
        KeyboardShortcutEntry(shortcut: "Cmd+6", description: "Go to Tools", category: .navigation),
        KeyboardShortcutEntry(shortcut: "Cmd+7", description: "Go to Templates", category: .navigation),
        KeyboardShortcutEntry(shortcut: "Cmd+8", description: "Go to Logs", category: .navigation),
        KeyboardShortcutEntry(shortcut: "Cmd+,", description: "Open Settings", category: .navigation),

        // Actions
        KeyboardShortcutEntry(shortcut: "Cmd+K", description: "Open Command Palette", category: .actions),
        KeyboardShortcutEntry(shortcut: "Shift+Cmd+R", description: "Start Infrastructure", category: .actions),
        KeyboardShortcutEntry(shortcut: "Shift+Cmd+S", description: "Stop Infrastructure", category: .actions),
        KeyboardShortcutEntry(shortcut: "Shift+Cmd+N", description: "Add New Project", category: .actions),
        KeyboardShortcutEntry(shortcut: "Cmd+R", description: "Refresh Current View", category: .actions),

        // General
        KeyboardShortcutEntry(shortcut: "Cmd+W", description: "Close Window", category: .general),
        KeyboardShortcutEntry(shortcut: "Cmd+Q", description: "Quit DevFlow", category: .general),
        KeyboardShortcutEntry(shortcut: "Cmd+M", description: "Minimize Window", category: .general),
        KeyboardShortcutEntry(shortcut: "Escape", description: "Close Dialog/Cancel", category: .general),
    ]

    private var filteredShortcuts: [KeyboardShortcutEntry] {
        shortcuts.filter { entry in
            let matchesSearch = searchText.isEmpty ||
                entry.description.localizedCaseInsensitiveContains(searchText) ||
                entry.shortcut.localizedCaseInsensitiveContains(searchText)
            let matchesCategory = selectedCategory == nil || entry.category == selectedCategory
            return matchesSearch && matchesCategory
        }
    }

    private var groupedShortcuts: [(ShortcutCategory, [KeyboardShortcutEntry])] {
        ShortcutCategory.allCases.compactMap { category in
            let entries = filteredShortcuts.filter { $0.category == category }
            return entries.isEmpty ? nil : (category, entries)
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Search and filter
            HStack {
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    TextField("Search shortcuts...", text: $searchText)
                        .textFieldStyle(.plain)
                }
                .padding(8)
                .background(Color(nsColor: .textBackgroundColor))
                .cornerRadius(8)

                Picker("Category", selection: $selectedCategory) {
                    Text("All").tag(nil as ShortcutCategory?)
                    ForEach(ShortcutCategory.allCases, id: \.self) { category in
                        Text(category.rawValue).tag(category as ShortcutCategory?)
                    }
                }
                .pickerStyle(.menu)
                .frame(width: 140)
            }

            // Shortcuts list
            VStack(alignment: .leading, spacing: 20) {
                ForEach(groupedShortcuts, id: \.0) { category, entries in
                    VStack(alignment: .leading, spacing: 8) {
                        Text(category.rawValue)
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundStyle(.secondary)

                        VStack(spacing: 0) {
                            ForEach(entries) { entry in
                                ShortcutRow(entry: entry)
                                if entry.id != entries.last?.id {
                                    Divider()
                                }
                            }
                        }
                        .background(Color(nsColor: .textBackgroundColor))
                        .cornerRadius(8)
                    }
                }
            }
        }
        .accessibilityIdentifier("keyboardShortcutsView")
    }
}

/// A single row displaying a keyboard shortcut.
struct ShortcutRow: View {
    let entry: KeyboardShortcutEntry

    var body: some View {
        HStack {
            Text(entry.description)
                .foregroundStyle(.primary)

            Spacer()

            ShortcutBadge(shortcut: entry.shortcut)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
    }
}

/// Badge displaying a keyboard shortcut with styled keys.
struct ShortcutBadge: View {
    let shortcut: String

    var body: some View {
        HStack(spacing: 4) {
            ForEach(parseShortcut(shortcut), id: \.self) { key in
                Text(key)
                    .font(.system(.caption, design: .rounded))
                    .fontWeight(.medium)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 3)
                    .background(Color(nsColor: .controlBackgroundColor))
                    .cornerRadius(4)
                    .overlay(
                        RoundedRectangle(cornerRadius: 4)
                            .strokeBorder(Color(nsColor: .separatorColor), lineWidth: 0.5)
                    )
            }
        }
    }

    private func parseShortcut(_ shortcut: String) -> [String] {
        shortcut
            .replacingOccurrences(of: "Cmd", with: "\u{2318}")
            .replacingOccurrences(of: "Shift", with: "\u{21E7}")
            .replacingOccurrences(of: "Alt", with: "\u{2325}")
            .replacingOccurrences(of: "Ctrl", with: "\u{2303}")
            .components(separatedBy: "+")
    }
}

#Preview {
    KeyboardShortcutsView()
        .padding()
        .frame(width: 500, height: 500)
}

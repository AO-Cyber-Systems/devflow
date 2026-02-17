import SwiftUI

struct DatabaseView: View {
    @Environment(AppState.self) private var appState
    @State private var searchText = ""

    var filteredDatabases: [Database] {
        if searchText.isEmpty {
            return appState.databases
        }
        return appState.databases.filter {
            $0.name.localizedCaseInsensitiveContains(searchText)
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Databases")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    Text("Manage local development databases")
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Button {
                    appState.showAddDatabase = true
                } label: {
                    Label("Add Database", systemImage: "plus")
                }
                .buttonStyle(.borderedProminent)
                .accessibilityIdentifier("addDatabaseButton")
            }
            .padding(24)

            Divider()

            // Search
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                TextField("Search databases...", text: $searchText)
                    .textFieldStyle(.plain)
                    .accessibilityIdentifier("databaseSearchField")
            }
            .padding(8)
            .background(Color(nsColor: .controlBackgroundColor))
            .cornerRadius(8)
            .padding(.horizontal, 24)
            .padding(.vertical, 12)

            // Database List
            if appState.isLoadingDatabases && appState.databases.isEmpty {
                VStack {
                    Spacer()
                    ProgressView("Loading databases...")
                    Spacer()
                }
            } else if filteredDatabases.isEmpty {
                VStack(spacing: 12) {
                    Spacer()
                    Image(systemName: searchText.isEmpty ? "cylinder.split.1x2" : "magnifyingglass")
                        .font(.system(size: 40))
                        .foregroundStyle(.secondary)
                    Text(searchText.isEmpty ? "No databases" : "No matching databases")
                        .font(.headline)
                    if searchText.isEmpty {
                        Text("Add a database to get started")
                            .foregroundStyle(.secondary)
                        Button("Add Database") {
                            appState.showAddDatabase = true
                        }
                        .accessibilityIdentifier("emptyStateAddDatabaseButton")
                    }
                    Spacer()
                }
                .frame(maxWidth: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(filteredDatabases) { database in
                            DatabaseCard(database: database)
                                .accessibilityIdentifier("databaseCard_\(database.id)")
                        }
                    }
                    .padding(24)
                }
            }
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .accessibilityIdentifier("databaseView")
        .task {
            await appState.loadDatabases()
        }
    }
}

struct DatabaseCard: View {
    let database: Database
    @Environment(AppState.self) private var appState
    @State private var showDeleteConfirmation = false
    @State private var showConnectionString = false

    var typeColor: Color {
        switch database.type {
        case .postgres: return .blue
        case .mysql: return .orange
        case .redis: return .red
        case .mongodb: return .green
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Header row
            HStack {
                // Type icon
                Image(systemName: database.type.icon)
                    .font(.title2)
                    .frame(width: 40, height: 40)
                    .background(typeColor.opacity(0.1))
                    .foregroundStyle(typeColor)
                    .cornerRadius(8)

                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(database.name)
                            .font(.headline)
                        StatusBadge(isRunning: database.isRunning, size: .small)
                    }
                    Text(database.type.displayName)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                // Actions
                HStack(spacing: 8) {
                    Button {
                        Task {
                            if database.isRunning {
                                await appState.stopDatabase(database)
                            } else {
                                await appState.startDatabase(database)
                            }
                        }
                    } label: {
                        Image(systemName: database.isRunning ? "stop.fill" : "play.fill")
                    }
                    .buttonStyle(.bordered)
                    .tint(database.isRunning ? .red : .green)
                    .accessibilityIdentifier("toggleDatabase_\(database.id)")

                    Button(role: .destructive) {
                        showDeleteConfirmation = true
                    } label: {
                        Image(systemName: "trash")
                    }
                    .buttonStyle(.bordered)
                    .accessibilityIdentifier("deleteDatabase_\(database.id)")
                }
            }

            Divider()

            // Connection info
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Host")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text("\(database.host):\(database.port)")
                        .font(.system(.body, design: .monospaced))
                }

                Spacer()

                if let connectionString = database.connectionString {
                    Button {
                        showConnectionString.toggle()
                    } label: {
                        Label(
                            showConnectionString ? "Hide" : "Show Connection String",
                            systemImage: showConnectionString ? "eye.slash" : "eye"
                        )
                    }
                    .buttonStyle(.borderless)
                    .font(.caption)
                    .accessibilityIdentifier("toggleConnectionString_\(database.id)")
                }
            }

            if showConnectionString, let connectionString = database.connectionString {
                HStack {
                    Text(connectionString)
                        .font(.system(.caption, design: .monospaced))
                        .textSelection(.enabled)
                        .lineLimit(1)

                    Button {
                        NSPasteboard.general.clearContents()
                        NSPasteboard.general.setString(connectionString, forType: .string)
                    } label: {
                        Image(systemName: "doc.on.doc")
                    }
                    .buttonStyle(.borderless)
                    .help("Copy to clipboard")
                    .accessibilityIdentifier("copyConnectionString_\(database.id)")
                }
                .padding(8)
                .background(Color(nsColor: .controlBackgroundColor))
                .cornerRadius(4)
            }
        }
        .padding()
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(12)
        .confirmationDialog(
            "Delete Database",
            isPresented: $showDeleteConfirmation,
            titleVisibility: .visible
        ) {
            Button("Delete", role: .destructive) {
                Task {
                    await appState.deleteDatabase(database)
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Are you sure you want to delete '\(database.name)'? This will remove all data.")
        }
    }
}

struct AddDatabaseSheet: View {
    @Environment(AppState.self) private var appState
    @Environment(\.dismiss) private var dismiss

    @State private var name = ""
    @State private var type: DatabaseType = .postgres

    var isValid: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty
    }

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("Add Database")
                        .font(.headline)
                    Spacer()
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                    .accessibilityIdentifier("closeAddDatabaseButton")
                }
                .padding()

                Divider()

                // Form
                VStack(alignment: .leading, spacing: 20) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Database Name")
                            .fontWeight(.medium)
                        TextField("my-database", text: $name)
                            .textFieldStyle(.roundedBorder)
                            .accessibilityIdentifier("databaseNameField")
                    }

                    VStack(alignment: .leading, spacing: 6) {
                        Text("Database Type")
                            .fontWeight(.medium)

                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 12) {
                            ForEach(DatabaseType.allCases) { dbType in
                                DatabaseTypeOption(
                                    type: dbType,
                                    isSelected: type == dbType
                                ) {
                                    type = dbType
                                }
                            }
                        }
                    }

                    // Info about selected type
                    HStack {
                        Image(systemName: "info.circle")
                            .foregroundStyle(.blue)
                        Text("Default port: \(type.defaultPort)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(8)
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(6)
                }
                .padding()

                Spacer(minLength: 20)

                Divider()

                // Actions
                HStack {
                    Button("Cancel") {
                        dismiss()
                    }
                    .keyboardShortcut(.cancelAction)
                    .accessibilityIdentifier("cancelAddDatabaseButton")

                    Spacer()

                    Button("Create Database") {
                        Task {
                            await appState.createDatabase(name: name, type: type)
                            dismiss()
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(!isValid)
                    .keyboardShortcut(.defaultAction)
                    .accessibilityIdentifier("confirmAddDatabaseButton")
                }
                .padding()
            }
        }
        .frame(width: 400, height: 420)
        .accessibilityIdentifier("addDatabaseSheet")
    }
}

struct DatabaseTypeOption: View {
    let type: DatabaseType
    let isSelected: Bool
    let action: () -> Void

    var typeColor: Color {
        switch type {
        case .postgres: return .blue
        case .mysql: return .orange
        case .redis: return .red
        case .mongodb: return .green
        }
    }

    var body: some View {
        Button(action: action) {
            HStack {
                Image(systemName: type.icon)
                    .font(.title3)
                    .foregroundStyle(typeColor)

                VStack(alignment: .leading) {
                    Text(type.displayName)
                        .font(.subheadline)
                        .fontWeight(.medium)
                    Text("Port \(type.defaultPort)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.blue)
                }
            }
            .padding(12)
            .background(isSelected ? Color.blue.opacity(0.1) : Color(nsColor: .controlBackgroundColor))
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(isSelected ? Color.blue : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier("databaseType_\(type.rawValue)")
    }
}

#Preview {
    DatabaseView()
        .environment(AppState())
        .frame(width: 800, height: 600)
}

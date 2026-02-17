import SwiftUI

/// Grid view showing project services with their status.
struct ServicesGridView: View {
    let services: [ProjectService]
    @Environment(AppState.self) private var appState

    private let columns = [
        GridItem(.adaptive(minimum: 180, maximum: 250), spacing: 12)
    ]

    var body: some View {
        if services.isEmpty {
            EmptyServicesView()
        } else {
            LazyVGrid(columns: columns, spacing: 12) {
                ForEach(services) { service in
                    ServiceCard(service: service)
                }
            }
        }
    }
}

struct ServiceCard: View {
    let service: ProjectService

    var statusColor: Color {
        switch service.statusColor {
        case "green": return .green
        case "orange": return .orange
        case "red": return .red
        default: return .secondary
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)

                Text(service.name)
                    .font(.headline)
                    .lineLimit(1)

                Spacer()

                if let health = service.health {
                    Image(systemName: health == "healthy" ? "heart.fill" : "heart.slash")
                        .font(.caption)
                        .foregroundStyle(health == "healthy" ? .green : .orange)
                }
            }

            Text(service.image)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(1)

            HStack {
                Text(service.status)
                    .font(.caption2)
                    .foregroundStyle(statusColor)

                Spacer()

                if !service.ports.isEmpty {
                    HStack(spacing: 4) {
                        Image(systemName: "network")
                            .font(.caption2)
                        Text(service.ports.joined(separator: ", "))
                            .font(.caption2)
                    }
                    .foregroundStyle(.secondary)
                }
            }
        }
        .padding(12)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(8)
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(statusColor.opacity(0.3), lineWidth: 1)
        )
        .accessibilityIdentifier("serviceCard_\(service.name)")
    }
}

struct EmptyServicesView: View {
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: "shippingbox")
                .font(.title)
                .foregroundStyle(.secondary)
            Text("No services found")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Text("Add a docker-compose.yml to define services")
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
    }
}

#Preview {
    ServicesGridView(services: [
        ProjectService(
            name: "web",
            status: "Up 2 hours",
            image: "node:20-alpine",
            containerId: "abc123",
            ports: ["3000:3000"],
            health: "healthy"
        ),
        ProjectService(
            name: "db",
            status: "Up 2 hours",
            image: "postgres:16",
            containerId: "def456",
            ports: ["5432:5432"],
            health: nil
        ),
        ProjectService(
            name: "redis",
            status: "Exited (0)",
            image: "redis:7",
            containerId: nil,
            ports: [],
            health: nil
        ),
    ])
    .environment(AppState())
    .padding()
    .frame(width: 500)
}

import SwiftUI

/// Table view showing port mappings for a project.
struct PortsTableView: View {
    let ports: [PortMapping]

    var body: some View {
        if ports.isEmpty {
            EmptyPortsView()
        } else {
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("Service")
                        .frame(width: 100, alignment: .leading)
                    Text("Host")
                        .frame(width: 80, alignment: .leading)
                    Text("Container")
                        .frame(width: 80, alignment: .leading)
                    Text("IP")
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .font(.caption)
                .fontWeight(.medium)
                .foregroundStyle(.secondary)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color(nsColor: .controlBackgroundColor))

                Divider()

                // Rows
                ForEach(ports) { port in
                    PortRow(port: port)
                    if port.id != ports.last?.id {
                        Divider()
                            .padding(.leading, 12)
                    }
                }
            }
            .background(Color(nsColor: .textBackgroundColor))
            .cornerRadius(8)
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color(nsColor: .separatorColor), lineWidth: 1)
            )
        }
    }
}

struct PortRow: View {
    let port: PortMapping

    var body: some View {
        HStack {
            Text(port.service)
                .frame(width: 100, alignment: .leading)
                .lineLimit(1)

            HStack(spacing: 4) {
                Text("\(port.hostPort)")
                    .font(.system(.body, design: .monospaced))
                Button {
                    if let url = URL(string: "http://localhost:\(port.hostPort)") {
                        NSWorkspace.shared.open(url)
                    }
                } label: {
                    Image(systemName: "arrow.up.forward.square")
                        .font(.caption)
                }
                .buttonStyle(.borderless)
            }
            .frame(width: 80, alignment: .leading)

            Text("\(port.containerPort)")
                .font(.system(.body, design: .monospaced))
                .frame(width: 80, alignment: .leading)

            Text(port.hostIp)
                .font(.caption)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .accessibilityIdentifier("portRow_\(port.hostPort)")
    }
}

struct EmptyPortsView: View {
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "network.slash")
                .foregroundStyle(.secondary)
            Text("No port mappings")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(8)
    }
}

#Preview {
    PortsTableView(ports: [
        PortMapping(service: "web", hostPort: 3000, containerPort: 3000, hostIp: "0.0.0.0"),
        PortMapping(service: "db", hostPort: 5432, containerPort: 5432, hostIp: "127.0.0.1"),
        PortMapping(service: "redis", hostPort: 6379, containerPort: 6379, hostIp: "0.0.0.0"),
    ])
    .padding()
    .frame(width: 500)
}

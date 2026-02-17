import SwiftUI

struct InfrastructureView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Infrastructure")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        Text("Manage your development infrastructure")
                            .foregroundStyle(.secondary)
                    }

                    Spacer()

                    HStack(spacing: 12) {
                        Button {
                            Task { await appState.refreshInfraStatus() }
                        } label: {
                            Label("Refresh", systemImage: "arrow.clockwise")
                        }
                        .accessibilityIdentifier("refreshInfraButton")

                        Button {
                            Task {
                                if appState.infraStatus.allRunning {
                                    await appState.stopInfrastructure()
                                } else {
                                    await appState.startInfrastructure()
                                }
                            }
                        } label: {
                            if appState.isLoadingInfra {
                                ProgressView()
                                    .scaleEffect(0.7)
                            } else {
                                Label(
                                    appState.infraStatus.allRunning ? "Stop All" : "Start All",
                                    systemImage: appState.infraStatus.allRunning ? "stop.fill" : "play.fill"
                                )
                            }
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(appState.infraStatus.allRunning ? .red : .green)
                        .disabled(appState.isLoadingInfra)
                        .accessibilityIdentifier("toggleAllInfraButton")
                    }
                }

                // Status Cards
                VStack(spacing: 16) {
                    // Network Status
                    StatusCard(
                        title: "Docker Network",
                        icon: "network",
                        isRunning: appState.infraStatus.networkExists,
                        detail: appState.infraStatus.networkName,
                        isLoading: appState.isLoadingInfra
                    )

                    // Traefik Status
                    StatusCard(
                        title: "Traefik Proxy",
                        icon: "arrow.triangle.branch",
                        isRunning: appState.infraStatus.traefikRunning,
                        detail: appState.infraStatus.traefikUrl,
                        isLoading: appState.isLoadingInfra
                    )

                    // Remote Status (if configured)
                    if appState.infraStatus.remoteConfigured {
                        StatusCard(
                            title: "Remote Connection",
                            icon: "cloud",
                            isRunning: appState.infraStatus.tunnelStatus == "connected",
                            detail: appState.infraStatus.remoteHost,
                            isLoading: appState.isLoadingInfra
                        )
                    }
                }

                // Domains & SSL Section
                DomainsSection()

                // Registered Projects
                if !appState.infraStatus.registeredProjects.isEmpty {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Registered Projects")
                            .font(.headline)

                        ForEach(appState.infraStatus.registeredProjects) { project in
                            HStack {
                                Image(systemName: "folder")
                                    .foregroundStyle(.secondary)
                                VStack(alignment: .leading) {
                                    Text(project.name)
                                    Text(project.path)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                            }
                            .padding(.vertical, 4)
                        }
                    }
                    .padding()
                    .background(Color(nsColor: .controlBackgroundColor))
                    .cornerRadius(12)
                }

                // Traefik Dashboard Link
                if appState.infraStatus.traefikRunning {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Traefik Dashboard")
                            .font(.headline)

                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Access the Traefik dashboard to view routes and middleware")
                                    .foregroundStyle(.secondary)
                                Text("http://localhost:\(appState.globalConfig.traefikDashboardPort)")
                                    .font(.system(.body, design: .monospaced))
                                    .foregroundStyle(.blue)
                            }

                            Spacer()

                            Button {
                                if let url = URL(string: "http://localhost:\(appState.globalConfig.traefikDashboardPort)") {
                                    NSWorkspace.shared.open(url)
                                }
                            } label: {
                                Label("Open", systemImage: "arrow.up.forward.square")
                            }
                            .accessibilityIdentifier("openTraefikDashboardButton")
                        }
                        .padding()
                        .background(Color(nsColor: .controlBackgroundColor))
                        .cornerRadius(12)
                    }
                }
            }
            .padding(24)
        }
        .background(Color(nsColor: .windowBackgroundColor))
        .accessibilityIdentifier("infrastructureView")
        .task {
            await appState.loadDomains()
        }
    }
}

// MARK: - Domains Section

struct DomainsSection: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Section Header
            HStack {
                Text("Domains & SSL")
                    .font(.headline)

                Spacer()

                Button {
                    appState.showAddDomain = true
                } label: {
                    Label("Add Domain", systemImage: "plus")
                }
                .accessibilityIdentifier("addDomainButton")
            }

            // Certificate Status
            CertificateStatusCard()

            // Managed Domains List
            if appState.isLoadingDomains {
                HStack {
                    ProgressView()
                        .scaleEffect(0.7)
                    Text("Loading domains...")
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .center)
                .padding()
            } else if appState.domainStatuses.isEmpty {
                Text("No domains configured")
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding()
            } else {
                VStack(spacing: 8) {
                    ForEach(appState.domainStatuses) { domain in
                        DomainRow(domain: domain)
                    }
                }
            }

            // DNS Status Warning
            if appState.domainsNeedingHostsEntry > 0 {
                DNSWarningCard(count: appState.domainsNeedingHostsEntry)
            }
        }
        .padding()
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(12)
        .sheet(isPresented: Binding(
            get: { appState.showAddDomain },
            set: { appState.showAddDomain = $0 }
        )) {
            AddDomainSheet()
        }
    }
}

// MARK: - Certificate Status Card

struct CertificateStatusCard: View {
    @Environment(AppState.self) private var appState

    var certInfo: CertificateInfo {
        appState.certificateInfo
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                // Status icon
                Image(systemName: certInfo.valid ? "checkmark.shield.fill" : "xmark.shield.fill")
                    .font(.title2)
                    .foregroundStyle(certInfo.valid ? .green : .red)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Certificate Status")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                    if certInfo.valid {
                        Text("Valid until \(certInfo.expiresAtFormatted)")
                            .font(.headline)
                    } else {
                        Text("No valid certificate")
                            .font(.headline)
                            .foregroundStyle(.red)
                    }
                }

                Spacer()

                Button {
                    Task {
                        await appState.regenerateCertificates()
                    }
                } label: {
                    if appState.isRegeneratingCerts {
                        ProgressView()
                            .scaleEffect(0.7)
                    } else {
                        Label("Regenerate", systemImage: "arrow.clockwise")
                    }
                }
                .disabled(appState.isRegeneratingCerts)
                .accessibilityIdentifier("regenerateCertsButton")
            }

            if certInfo.valid && !certInfo.domains.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Covers:")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(certInfo.domainsDisplay)
                        .font(.system(.caption, design: .monospaced))
                        .foregroundStyle(.secondary)
                }
            }

            if !certInfo.path.isEmpty {
                HStack(spacing: 4) {
                    Text("Path:")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(certInfo.path)
                        .font(.system(.caption, design: .monospaced))
                        .foregroundStyle(.tertiary)
                        .lineLimit(1)
                        .truncationMode(.middle)
                }
            }
        }
        .padding()
        .background(Color(nsColor: .windowBackgroundColor))
        .cornerRadius(8)
    }
}

// MARK: - Domain Row

struct DomainRow: View {
    @Environment(AppState.self) private var appState
    let domain: DomainStatus

    var body: some View {
        HStack(spacing: 12) {
            // Domain name
            VStack(alignment: .leading, spacing: 2) {
                Text(domain.domain)
                    .font(.system(.body, design: .monospaced))

                HStack(spacing: 8) {
                    // Source badge
                    Text(domain.sourceDisplay)
                        .font(.caption2)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(domain.isDefault ? Color.blue.opacity(0.1) : Color.gray.opacity(0.1))
                        .foregroundStyle(domain.isDefault ? .blue : .secondary)
                        .cornerRadius(4)

                    if domain.isWildcard {
                        Text("Wildcard")
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.purple.opacity(0.1))
                            .foregroundStyle(.purple)
                            .cornerRadius(4)
                    }
                }
            }

            Spacer()

            // SSL Status
            HStack(spacing: 4) {
                Image(systemName: domain.inCertificate ? "lock.fill" : "lock.open")
                    .font(.caption)
                Text("SSL")
                    .font(.caption)
            }
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(domain.inCertificate ? Color.green.opacity(0.1) : Color.orange.opacity(0.1))
            .foregroundStyle(domain.inCertificate ? .green : .orange)
            .cornerRadius(4)

            // DNS Status (non-wildcards only)
            if !domain.isWildcard {
                HStack(spacing: 4) {
                    Image(systemName: domain.inHostsFile ? "checkmark" : "xmark")
                        .font(.caption)
                    Text("DNS")
                        .font(.caption)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(domain.inHostsFile ? Color.green.opacity(0.1) : Color.orange.opacity(0.1))
                .foregroundStyle(domain.inHostsFile ? .green : .orange)
                .cornerRadius(4)
            }

            // Remove button (only for non-default domains)
            if !domain.isDefault {
                Button {
                    Task {
                        await appState.removeDomain(domain.domain)
                    }
                } label: {
                    Image(systemName: "trash")
                        .foregroundStyle(.red)
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("removeDomain-\(domain.domain)")
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color(nsColor: .windowBackgroundColor))
        .cornerRadius(6)
    }
}

// MARK: - DNS Warning Card

struct DNSWarningCard: View {
    @Environment(AppState.self) private var appState
    let count: Int

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(.orange)

            VStack(alignment: .leading, spacing: 2) {
                Text("\(count) domain\(count == 1 ? "" : "s") need\(count == 1 ? "s" : "") /etc/hosts entries")
                    .font(.subheadline)
                Text("Use *.localhost for automatic resolution")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button {
                Task {
                    await appState.updateHostsFile()
                }
            } label: {
                Text("Update Hosts")
            }
            .accessibilityIdentifier("updateHostsButton")
        }
        .padding()
        .background(Color.orange.opacity(0.1))
        .cornerRadius(8)
    }
}

// MARK: - Status Card

struct StatusCard: View {
    let title: String
    let icon: String
    let isRunning: Bool
    let detail: String?
    let isLoading: Bool

    var body: some View {
        HStack(spacing: 16) {
            // Icon
            Image(systemName: icon)
                .font(.title2)
                .frame(width: 40, height: 40)
                .background(isRunning ? Color.green.opacity(0.1) : Color.secondary.opacity(0.1))
                .foregroundStyle(isRunning ? .green : .secondary)
                .cornerRadius(8)

            // Info
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                if let detail = detail {
                    Text(detail)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }

            Spacer()

            // Status
            if isLoading {
                ProgressView()
                    .scaleEffect(0.7)
            } else {
                StatusBadge(isRunning: isRunning)
            }
        }
        .padding()
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(12)
    }
}

#Preview {
    InfrastructureView()
        .environment(AppState())
        .frame(width: 900, height: 700)
}

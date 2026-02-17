// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "DevFlow",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        .executable(name: "DevFlow", targets: ["DevFlow"])
    ],
    dependencies: [
        .package(url: "https://github.com/swiftlang/swift-subprocess.git", from: "0.1.0")
    ],
    targets: [
        .executableTarget(
            name: "DevFlow",
            dependencies: [
                .product(name: "Subprocess", package: "swift-subprocess")
            ],
            path: "DevFlow"
        ),
        .testTarget(
            name: "DevFlowTests",
            dependencies: ["DevFlow"],
            path: "DevFlowTests"
        )
    ]
)

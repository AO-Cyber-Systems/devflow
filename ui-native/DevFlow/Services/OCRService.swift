import Foundation
import Vision

#if canImport(AppKit)
import AppKit
#endif

/// Service for extracting text from images and PDFs using Apple's Vision framework.
@MainActor
class OCRService {
    // MARK: - Singleton

    static let shared = OCRService()

    private init() {}

    // MARK: - Public API

    /// Extract text from an image file.
    func extractText(from imageURL: URL) async throws -> String {
        guard let cgImage = loadCGImage(from: imageURL) else {
            throw OCRError.failedToLoadImage
        }

        return try await extractText(from: cgImage)
    }

    /// Extract text from a CGImage.
    func extractText(from image: CGImage) async throws -> String {
        return try await withCheckedThrowingContinuation { continuation in
            let request = VNRecognizeTextRequest { request, error in
                if let error = error {
                    continuation.resume(throwing: error)
                    return
                }

                guard let observations = request.results as? [VNRecognizedTextObservation] else {
                    continuation.resume(returning: "")
                    return
                }

                let text = observations.compactMap { observation in
                    observation.topCandidates(1).first?.string
                }.joined(separator: "\n")

                continuation.resume(returning: text)
            }

            // Configure for best accuracy
            request.recognitionLevel = .accurate
            request.usesLanguageCorrection = true

            let handler = VNImageRequestHandler(cgImage: image, options: [:])
            do {
                try handler.perform([request])
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }

    /// Extract text from a PDF file, returning text for each page.
    func extractTextFromPDF(_ pdfURL: URL) async throws -> [String] {
        guard let pdfDocument = CGPDFDocument(pdfURL as CFURL) else {
            throw OCRError.failedToLoadPDF
        }

        var pages: [String] = []

        for pageIndex in 1...pdfDocument.numberOfPages {
            guard let page = pdfDocument.page(at: pageIndex) else {
                pages.append("")
                continue
            }

            // Render page to image
            let pageRect = page.getBoxRect(.mediaBox)
            let scale: CGFloat = 2.0 // Higher scale for better OCR

            let width = Int(pageRect.width * scale)
            let height = Int(pageRect.height * scale)

            guard let context = CGContext(
                data: nil,
                width: width,
                height: height,
                bitsPerComponent: 8,
                bytesPerRow: 0,
                space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
            ) else {
                pages.append("")
                continue
            }

            context.setFillColor(CGColor.white)
            context.fill(CGRect(x: 0, y: 0, width: width, height: height))

            context.scaleBy(x: scale, y: scale)
            context.drawPDFPage(page)

            guard let cgImage = context.makeImage() else {
                pages.append("")
                continue
            }

            do {
                let text = try await extractText(from: cgImage)
                pages.append(text)
            } catch {
                pages.append("")
            }
        }

        return pages
    }

    /// Extract text with bounding boxes for structured document analysis.
    func extractTextWithBounds(from image: CGImage) async throws -> [TextRegion] {
        return try await withCheckedThrowingContinuation { continuation in
            let request = VNRecognizeTextRequest { request, error in
                if let error = error {
                    continuation.resume(throwing: error)
                    return
                }

                guard let observations = request.results as? [VNRecognizedTextObservation] else {
                    continuation.resume(returning: [])
                    return
                }

                let regions = observations.compactMap { observation -> TextRegion? in
                    guard let candidate = observation.topCandidates(1).first else {
                        return nil
                    }
                    return TextRegion(
                        text: candidate.string,
                        bounds: observation.boundingBox,
                        confidence: candidate.confidence
                    )
                }

                continuation.resume(returning: regions)
            }

            request.recognitionLevel = .accurate
            request.usesLanguageCorrection = true

            let handler = VNImageRequestHandler(cgImage: image, options: [:])
            do {
                try handler.perform([request])
            } catch {
                continuation.resume(throwing: error)
            }
        }
    }

    // MARK: - Private Helpers

    private func loadCGImage(from url: URL) -> CGImage? {
        #if canImport(AppKit)
        guard let nsImage = NSImage(contentsOf: url),
              let cgImage = nsImage.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
            return nil
        }
        return cgImage
        #else
        return nil
        #endif
    }
}

// MARK: - Supporting Types

struct TextRegion: Identifiable {
    let id = UUID()
    let text: String
    let bounds: CGRect
    let confidence: Float
}

enum OCRError: Error, LocalizedError {
    case failedToLoadImage
    case failedToLoadPDF
    case recognitionFailed

    var errorDescription: String? {
        switch self {
        case .failedToLoadImage:
            return "Failed to load image file"
        case .failedToLoadPDF:
            return "Failed to load PDF file"
        case .recognitionFailed:
            return "Text recognition failed"
        }
    }
}

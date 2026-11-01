#pragma once

#include <M5Dial.h>
#include <esp_partition.h>
#include <esp_spi_flash.h>

#include <stdint.h>

enum class FrameEncoding : uint8_t { RGB565 = 0, JPEG = 1 };
enum class FrameStorage : uint8_t { RuntimePreview = 0, FlashPartition = 1 };

struct FrameAssetProfile {
  uint16_t width = 240;
  uint16_t height = 240;
  uint16_t frameCount = 0;
  FrameEncoding encoding = FrameEncoding::RGB565;
  FrameStorage storage = FrameStorage::RuntimePreview;
  uint32_t bytes = 0;
  uint32_t largestFrameBytes = 0;
  bool finalArtwork = false;
};

// Implement this interface to replace the visual asset pack without changing App or RotationModel.
class IFrameAssetSource {
 public:
  virtual ~IFrameAssetSource() = default;
  virtual FrameAssetProfile profile() const = 0;
  virtual bool drawFrame(M5GFX& display, uint16_t frameIndex) = 0;
};

// Diagnostic renderer source used until the separately produced artwork is installed.
class PreviewFrameSource final : public IFrameAssetSource {
 public:
  FrameAssetProfile profile() const override;
  bool drawFrame(M5GFX& display, uint16_t frameIndex) override;
};

// Read-only, memory-mapped package for fast frame access from a replaceable flash partition.
class FlashMappedFrameSource final : public IFrameAssetSource {
 public:
  bool begin(uint16_t expectedWidth = 240, uint16_t expectedHeight = 240);
  FrameAssetProfile profile() const override { return profile_; }
  bool drawFrame(M5GFX& display, uint16_t frameIndex) override;
  bool ready() const { return ready_; }

 private:
  static constexpr uint8_t kAssetPartitionSubtype = 0x40;
  static constexpr uint32_t kMaxJpegFrameBytes = 48U * 1024U;
  static constexpr uint32_t kMaxRgb565FrameBytes = 240U * 240U * 2U;
  static constexpr uint16_t kMaxFrames = 360;
  void releaseMapping();

  const esp_partition_t* partition_ = nullptr;
  const uint8_t* mappedPackage_ = nullptr;
  spi_flash_mmap_handle_t mmapHandle_ = 0;
  uint32_t mappedBytes_ = 0;
  uint32_t packageBytes_ = 0;
  uint32_t frameOffsets_[kMaxFrames] = {};
  uint32_t frameSizes_[kMaxFrames] = {};
  FrameAssetProfile profile_;
  bool ready_ = false;
};

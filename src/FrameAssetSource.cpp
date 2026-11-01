#include "FrameAssetSource.h"
#include "Rgb565AssetPush.h"

#include <esp_err.h>
#include <math.h>
#include <stdio.h>

namespace {
constexpr uint16_t kInk = 0x0862;
constexpr uint16_t kBrass = 0xB513;
constexpr uint16_t kPaleGold = 0xF5C7;
constexpr uint16_t kAmber = 0xFC80;
constexpr uint16_t kDimBlue = 0x212B;
constexpr uint16_t kPackageVersion = 1;
constexpr uint32_t kHeaderBytes = 18;
constexpr uint32_t kFrameEntryBytes = 8;

uint16_t le16(const uint8_t* p) {
  return static_cast<uint16_t>(p[0] | (static_cast<uint16_t>(p[1]) << 8));
}

uint32_t le32(const uint8_t* p) {
  return static_cast<uint32_t>(p[0]) |
         (static_cast<uint32_t>(p[1]) << 8) |
         (static_cast<uint32_t>(p[2]) << 16) |
         (static_cast<uint32_t>(p[3]) << 24);
}
}

void FlashMappedFrameSource::releaseMapping() {
  if (mappedPackage_ != nullptr) spi_flash_munmap(mmapHandle_);
  partition_ = nullptr;
  mappedPackage_ = nullptr;
  mmapHandle_ = 0;
  mappedBytes_ = 0;
  packageBytes_ = 0;
  ready_ = false;
}

FrameAssetProfile PreviewFrameSource::profile() const {
  FrameAssetProfile p;
  p.width = 240;
  p.height = 240;
  p.frameCount = 64;
  p.encoding = FrameEncoding::RGB565;
  p.storage = FrameStorage::RuntimePreview;
  p.bytes = 0;
  p.largestFrameBytes = 0;
  p.finalArtwork = false;
  return p;
}

bool PreviewFrameSource::drawFrame(M5GFX& display, uint16_t frameIndex) {
  // Deliberately labeled diagnostic art: only the frame marker moves until final assets arrive.
  constexpr int16_t cx = 120;
  constexpr int16_t cy = 116;
  display.fillScreen(kInk);
  display.drawCircle(cx, cy, 112, kBrass);
  display.drawCircle(cx, cy, 107, kDimBlue);
  display.drawCircle(cx, cy, 95, kBrass);
  display.drawCircle(cx, cy, 86, kDimBlue);
  display.fillCircle(cx, cy, 65, 0x1123);
  display.drawCircle(cx, cy, 65, kBrass);
  for (uint8_t i = 0; i < 16; ++i) {
    const float a = static_cast<float>(i) * 6.2831853f / 16.0f;
    const int16_t x0 = cx + static_cast<int16_t>(76.0f * cosf(a));
    const int16_t y0 = cy + static_cast<int16_t>(76.0f * sinf(a));
    const int16_t x1 = cx + static_cast<int16_t>((i % 4 == 0 ? 89.0f : 83.0f) * cosf(a));
    const int16_t y1 = cy + static_cast<int16_t>((i % 4 == 0 ? 89.0f : 83.0f) * sinf(a));
    display.drawLine(x0, y0, x1, y1, i % 4 == 0 ? kPaleGold : kBrass);
  }
  const float marker = static_cast<float>(frameIndex) * 6.2831853f / 64.0f - 1.5707963f;
  const int16_t mx = cx + static_cast<int16_t>(100.0f * cosf(marker));
  const int16_t my = cy + static_cast<int16_t>(100.0f * sinf(marker));
  display.fillCircle(mx, my, 4, kAmber);
  display.fillCircle(cx, cy, 24, kDimBlue);
  display.drawCircle(cx, cy, 24, kPaleGold);
  display.fillCircle(cx, cy, 7, kAmber);

  display.setTextDatum(middle_center);
  display.setTextColor(kAmber);
  display.setFont(&fonts::Orbitron_Light_24);
  display.setTextSize(0.62f);
  display.drawString("ART PREVIEW", cx, 33);
  display.setTextColor(kPaleGold);
  display.setFont(&fonts::Orbitron_Light_24);
  display.setTextSize(0.52f);
  display.drawString("NOT FINAL", cx, 205);
  char count[20];
  snprintf(count, sizeof(count), "FRAME %02u / 64", static_cast<unsigned>(frameIndex + 1));
  display.setTextColor(kBrass);
  display.drawString(count, cx, 224);
  return true;
}

bool FlashMappedFrameSource::begin(uint16_t expectedWidth, uint16_t expectedHeight) {
  releaseMapping();
  ready_ = false;
  profile_ = FrameAssetProfile{};
  partition_ = esp_partition_find_first(ESP_PARTITION_TYPE_DATA,
      static_cast<esp_partition_subtype_t>(kAssetPartitionSubtype), "assets");
  if (partition_ == nullptr || partition_->size < kHeaderBytes) return false;

  const auto invalidPackage = [this]() {
    releaseMapping();
    return false;
  };

  const void* mapped = nullptr;
  const esp_err_t mapError = esp_partition_mmap(partition_, 0, partition_->size,
      SPI_FLASH_MMAP_DATA, &mapped, &mmapHandle_);
  if (mapError != ESP_OK || mapped == nullptr) return invalidPackage();
  mappedPackage_ = static_cast<const uint8_t*>(mapped);
  mappedBytes_ = partition_->size;

  const uint8_t* header = mappedPackage_;
  if (header[0] != 'D' || header[1] != 'P' || header[2] != 'W' || header[3] != '1')
    return invalidPackage();
  const uint16_t version = le16(header + 4);
  const uint16_t width = le16(header + 6);
  const uint16_t height = le16(header + 8);
  const uint16_t count = le16(header + 10);
  const uint8_t encoding = header[12];
  const uint8_t flags = header[13];
  const uint32_t totalBytes = le32(header + 14);
  if (version != kPackageVersion || width != expectedWidth || height != expectedHeight ||
      count == 0 || count > kMaxFrames || totalBytes < kHeaderBytes || totalBytes > mappedBytes_ ||
      (encoding != static_cast<uint8_t>(FrameEncoding::JPEG) &&
       encoding != static_cast<uint8_t>(FrameEncoding::RGB565))) return invalidPackage();

  const uint32_t tableEnd = kHeaderBytes + static_cast<uint32_t>(count) * kFrameEntryBytes;
  if (tableEnd > totalBytes) return invalidPackage();
  uint32_t largest = 0;
  for (uint16_t i = 0; i < count; ++i) {
    const uint8_t* entry = mappedPackage_ + kHeaderBytes + i * kFrameEntryBytes;
    frameOffsets_[i] = le32(entry);
    frameSizes_[i] = le32(entry + 4);
    const uint32_t offset = frameOffsets_[i];
    const uint32_t size = frameSizes_[i];
    if (offset < tableEnd || offset > totalBytes || size > totalBytes - offset)
      return invalidPackage();
    if (encoding == static_cast<uint8_t>(FrameEncoding::JPEG)) {
      if (size < 4 || size > kMaxJpegFrameBytes) return invalidPackage();
    } else if (size != static_cast<uint32_t>(width) * height * 2U ||
               size > kMaxRgb565FrameBytes || (offset & 1U) != 0) {
      return invalidPackage();
    }
    if (size > largest) largest = size;
  }

  packageBytes_ = totalBytes;
  profile_.width = width;
  profile_.height = height;
  profile_.frameCount = count;
  profile_.encoding = static_cast<FrameEncoding>(encoding);
  profile_.storage = FrameStorage::FlashPartition;
  profile_.bytes = packageBytes_;
  profile_.largestFrameBytes = largest;
  profile_.finalArtwork = (flags & 0x01U) != 0;
  ready_ = true;
  return true;
}

bool FlashMappedFrameSource::drawFrame(M5GFX& display, uint16_t frameIndex) {
  if (!ready_ || frameIndex >= profile_.frameCount) return false;
  const uint8_t* frame = mappedPackage_ + frameOffsets_[frameIndex];
  const uint32_t size = frameSizes_[frameIndex];
  if (profile_.encoding == FrameEncoding::JPEG) {
    display.drawJpg(frame, size, 0, 0);
  } else {
    pushRgb565LittleEndian(display, 0, 0, profile_.width, profile_.height, frame);
  }
  return true;
}

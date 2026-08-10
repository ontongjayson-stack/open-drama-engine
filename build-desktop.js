/**
 * Open Drama Engine — Desktop Packaging Helper Script (build-desktop.js)
 * Prepares standalone build directory and packaging manifests.
 */

const fs = require('fs');
const path = require('path');

function verifyBuildAssets() {
  console.log('======================================================================');
  console.log('🎬 OPEN DRAMA ENGINE DESKTOP PACKAGING VERIFICATION');
  console.log('======================================================================');

  const requiredFiles = [
    'main.js',
    'server.js',
    'engine.js',
    'index.html',
    'index.css',
    'omnirouter.py',
    'render_engine.py',
    'engine_bridge.py',
    'package.json',
    'scifi_city_preview.jpg'
  ];

  let missing = 0;
  requiredFiles.forEach((file) => {
    const fullPath = path.join(__dirname, file);
    if (fs.existsSync(fullPath)) {
      const stats = fs.statSync(fullPath);
      console.log(`  ✓ [Verified] ${file.padEnd(24)} (${stats.size} bytes)`);
    } else {
      console.error(`  ✕ [MISSING]  ${file}`);
      missing++;
    }
  });

  if (missing > 0) {
    console.error(`\n❌ Build Verification Failed: ${missing} required file(s) missing.`);
    process.exit(1);
  }

  console.log('\n✅ All desktop app build files verified successfully!');
  console.log('   Ready for packaging via Electron-Builder ("npm run pack" / "npm run dist").');
  console.log('======================================================================');
}

verifyBuildAssets();

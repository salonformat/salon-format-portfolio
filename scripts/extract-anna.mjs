import sharp from 'sharp';

const source = process.argv[2];
const output = process.argv[3];

const { data, info } = await sharp(source)
  .extract({ left: 145, top: 155, width: 720, height: 835 })
  .ensureAlpha()
  .raw()
  .toBuffer({ resolveWithObject: true });

for (let i = 0; i < data.length; i += 4) {
  const whiteness = Math.min(data[i], data[i + 1], data[i + 2]);
  const alpha = Math.max(0, Math.min(255, (whiteness - 135) * 3));
  data[i] = 255;
  data[i + 1] = 255;
  data[i + 2] = 255;
  data[i + 3] = alpha;
}

await sharp(data, { raw: info })
  .trim({ background: { r: 255, g: 255, b: 255, alpha: 0 } })
  .png()
  .toFile(output);

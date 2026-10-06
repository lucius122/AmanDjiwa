// Gagal kalau komponen memakai warna atau ukuran hardcode, bukan token (CLAUDE.md §2).
// Nilai mentah hanya boleh ada di src/styles/ (tokens.css + gaya global prototipe).
// ponytail: regex per baris, tidak menangkap style={{ width: 240 }}; ganti ke lint rule kalau itu mulai kecolongan.
import { readdirSync, readFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const RULES = [
  [/#[0-9a-fA-F]{3,8}\b/, 'warna hex'],
  [/\b(rgba?|hsla?)\(/, 'warna rgb/hsl'],
  [/-\[[^\]]*(\d(px|rem|em|vh|vw)|#|rgb)[^\]]*\]/, 'nilai arbitrer Tailwind'],
];

const root = fileURLToPath(new URL('../src/', import.meta.url));
const files = readdirSync(root, { recursive: true })
  .map(String)
  .filter((f) => /\.(ts|tsx)$/.test(f) && !f.replace(/\\/g, '/').startsWith('styles/'));

let bad = 0;
for (const f of files) {
  readFileSync(join(root, f), 'utf8')
    .split('\n')
    .forEach((line, i) => {
      for (const [re, what] of RULES) {
        if (re.test(line)) {
          bad++;
          console.error(`${relative(process.cwd(), join(root, f))}:${i + 1}  ${what}: ${line.trim()}`);
        }
      }
    });
}
if (bad) {
  console.error(`\n${bad} pelanggaran. Pakai kelas token dari tailwind.config.ts / tokens.css.`);
  process.exit(1);
}
console.log(`check:tokens OK (${files.length} file)`);

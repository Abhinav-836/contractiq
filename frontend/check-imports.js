const fs = require('fs');
const path = require('path');

console.log('🔍 Checking import paths...\n');

const importsToCheck = [
  { import: '../../components/Card', path: 'src/components/Card.jsx' },
  { import: '../../components/Button', path: 'src/components/Button.jsx' },
  { import: '../../components/Badge', path: 'src/components/Badge.jsx' },
  { import: '../../components/Spinner', path: 'src/components/Spinner.jsx' },
  { import: '../../components/ui/Card', path: 'src/components/ui/Card.jsx' },
  { import: '../../components/ui/Button', path: 'src/components/ui/Button.jsx' },
  { import: '../../components/ui/Badge', path: 'src/components/ui/Badge.jsx' },
  { import: '../../components/ui/Spinner', path: 'src/components/ui/Spinner.jsx' },
];

importsToCheck.forEach(item => {
  const fullPath = path.join(__dirname, item.path);
  if (fs.existsSync(fullPath)) {
    console.log(`✅ Use: ${item.import}`);
    console.log(`   Found at: ${item.path}\n`);
  }
});
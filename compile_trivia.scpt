JsOsaDAS1.001.00bplist00�Vscript_�const app = Application.currentApplication()
app.includeStandardAdditions = true

const N = Application("Numbers")

const doc = N.documents.at(0)
const outPathStr = doc.file().toString().replace('.numbers', '.csv')
const folder = outPathStr.substring(0, outPathStr.lastIndexOf("/"))

const x = [outPathStr, folder]

doc.export({to: outPathStr, as: "CSV"})

app.doShellScript(`/Users/robert/.nix-profile/bin/fish -C 'cd "${folder}" ;and poetry run python questions_to_latex.py'`)

doc.name()                               jscr  ��ޭ
export function templateSub(template, substitutions, { errorOnMissingKeys } = { errorOnMissingKeys: false }) {
    const subRegex = /(?<!\\)\$(\w+)/g;
    if (errorOnMissingKeys) {
        return template.replace(subRegex, function (match) {
            if (!(match in substitutions)) {
                throw new Error(`Template string $${match} not found in substitutions`);
            }
            return substitutions[match];
        });
    }
    else {
        return template.replace(subRegex, match => { var _a; return (_a = substitutions[match]) !== null && _a !== void 0 ? _a : match; });
    }
}

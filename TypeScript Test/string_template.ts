export function templateSub(
	template: string,
	substitutions: { [key in string]: string },
	{ errorOnMissingKeys } = { errorOnMissingKeys: false },
): string {
	const subRegex = /(?<!\\)\$(\w+)/g;
	if (errorOnMissingKeys) {
		return template.replace(subRegex, function (match) {
			if (!(match in substitutions)) {
				throw new Error(`Template string $${match} not found in substitutions`);
			}
			return substitutions[match];
		});
	} else {
		return template.replace(subRegex, match => substitutions[match] ?? match);
	}
}

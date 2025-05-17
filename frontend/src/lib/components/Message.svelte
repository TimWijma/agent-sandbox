<script lang="ts">
	import hljs from 'highlight.js/lib/core';
	import python from 'highlight.js/lib/languages/python';
	import 'highlight.js/styles/github.css';

	hljs.registerLanguage('python', python);

	export let message: {
		role: 'user' | 'model';
		message: string;
		type: 'general' | 'calculator' | 'file';
	};

	const highlightCode = (code: string, language: string) => {
		if (code.startsWith('```python\n')) {
			code = code.slice('```python\n'.length);
		}
		if (code.endsWith('\n```')) {
			code = code.slice(0, -'\n```'.length);
		}

		console.log(`Highlighting code: ${code} with language: ${language}`);

		if (language === 'python') {
			let value = hljs.highlight(code, { language }).value;
			console.log(`Highlighted code: ${value}`);

			return value;
		}
		return code;
	};

	const messageColor = message.role === 'user' ? 'bg-blue-500' : 'bg-gray-200';
</script>

<div class="flex items-start space-x-2" class:flex-row-reverse={message.role === 'user'}>
	<div
		class="rounded-lg {messageColor} whitespace-break-spaces p-2
"
		class:text-white={message.role === 'user'}
	>
		{#if message.type === 'file'}
			{@html highlightCode(message.message, 'python')}
		{:else}
			{message.message}
		{/if}
	</div>
</div>

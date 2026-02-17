<script lang="ts">
	let count = 0;

	function increment() {
		count += 1;
	}
</script>

<main class="flex min-h-screen flex-col items-center justify-center p-24">
	<h1 class="text-4xl font-bold mb-4">Welcome to SvelteKit</h1>
	<p class="text-gray-600 mb-8">Get started by editing src/routes/+page.svelte</p>

	<button
		class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
		on:click={increment}
	>
		Count: {count}
	</button>
</main>

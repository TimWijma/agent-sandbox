<script lang="ts">
	import { Button } from "$lib/components/ui/button";
	import { Input } from "$lib/components/ui/input";
	// import { Icon } from 'lucide-svelte';
    import { Search, Bell, User } from '@lucide/svelte';
</script>

<div class="grid h-screen grid-cols-[250px_1fr] grid-rows-[auto_1fr]">
	<aside class="row-span-2 border-r border-gray-200 bg-gray-100 p-4">
		<nav>
			<ul class="space-y-4">
			</ul>
		</nav>
	</aside>

	<header
		class="col-start-2 flex items-center justify-end space-x-4 border-b border-gray-200 bg-white p-4"
	>
		<!-- <Button variant="ghost" size="icon" aria-label="Search">
            <Search />
		</Button>
		<Button variant="ghost" size="icon" aria-label="Notifications">
            <Bell />
		</Button>
		<Button variant="ghost" size="icon" aria-label="User">
            <User />
		</Button> -->
	</header>

	<main class="col-start-2 flex flex-col justify-between bg-white p-4">
		<div class="flex-1">
			
		</div>
		<div class="border-t border-gray-200 pt-4">
			<Input placeholder="Type your message here..." />
		</div>
	</main>
</div>

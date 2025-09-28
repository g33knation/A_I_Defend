<template>
  <div id="app">
    <h1>Defense AI Dashboard</h1>
    <p>Backend API: {{ backendMessage }}</p>
  </div>
</template>

<script>
export default {
  data() {
    return { backendMessage: "loading..." };
  },
  async created() {
    try {
      const res = await fetch("http://localhost:8000/");
      const json = await res.json();
      this.backendMessage = json.message;
    } catch (e) {
      this.backendMessage = "Backend not reachable";
    }
  }
};
</script>


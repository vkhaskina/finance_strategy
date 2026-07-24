<template>
  <div id="wrapper">
    <nav class="navbar is-dark">
      <div class="navbar-brand">

        <a class="navbar-burger" aria-label="menu" aria-expanded="false" data-target="navbar-menu">
          <span aria-hidden="true"></span>
          <span aria-hidden="true"></span>
          <span aria-hidden="true"></span>
        </a>
      </div>

      <div class="navbar-menu" id="navbar-menu">
        <div class="navbar-start">
          <router-link
            to="/"
            class="navbar-item"
            :class="{ 'is-active': $route.path === '/' }">
            Главная
          </router-link>
        </div>
      </div>
    </nav>

    <section class="section">
      <div class="container is-fluid">
        <router-view/>
      </div>
    </section>
  </div>

</template>

<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<style>
  @import "bulma/css/bulma.min.css";
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
  }

  #app, #wrapper {
    width: 100%;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .navbar {
    width: 100%;
    padding-left: 0;
    padding-right: 0;
    border-radius: 0;
  }

  .navbar-start {
    margin-left: 0;
    padding-left: 0.75rem;
  }

  .navbar-item {
    transition: all 0.2s ease;
    position: relative;
  }

  .navbar-item::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    width: 0;
    height: 2px;
    transition: all 0.2s ease;
    transform: translateX(-50%);
  }

  .navbar-item:hover::after {
    width: 80%;
  }

  .section {
    width: 100%;
    padding-left: 0;
    padding-right: 0;
    flex: 1;
    background: #f5f5f5;
  }
</style>


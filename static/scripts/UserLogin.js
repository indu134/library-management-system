// app.js

Vue.use(VueRouter);

const LoginComponent = {
  template: `
    <div>
      <h3 class="text-center">Login</h3>
      <form @submit.prevent="login">
        <div class="mb-3">
          <label for="username" class="form-label">Username</label>
          <input type="text" v-model="username" class="form-control" id="username" required>
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input type="password" v-model="password" class="form-control" id="password" required>
        </div>
        <div class="text-center">
          <button type="submit" class="btn btn-primary">Login</button>
        </div>
        <p class="mt-3">Don't have an account? <router-link to="/register">Register</router-link></p>
      </form>
    </div>
  `,
  data() {
    return {
      username: '',
      password: ''
    };
  },
  methods: {
    login() {
        axios.post('/api/login', {
            username: this.username,
            password: this.password,
          })
          .then(response => {
            console.log(response.data);
            localStorage.setItem('token', response.data.token);
            // Redirect or perform other actions as needed
            this.$router.push("/dashBoard")
          })
          .catch(error => {
            console.error('Login failed:', error.response.data.message);
          });
    }
  }
};

const RegistrationComponent = {
  template: `
    <div>
      <h3 class="text-center">Registration</h3>
      <form @submit.prevent="register">
        <div class="mb-3">
          <label for="username" class="form-label">Username</label>
          <input type="text" v-model="username" class="form-control" id="username" required>
        </div>
        <div class="mb-3">
          <label for="email" class="form-label">Email</label>
          <input type="email" v-model="email" class="form-control" id="email" required>
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Password</label>
          <input type="password" v-model="password" class="form-control" id="password" required>
        </div>
        <div class="text-center">
          <button type="submit" class="btn btn-primary">Register</button>
        </div>
      </form>
      <p class="mt-3">Already have an account? <router-link to="/login">Login</router-link></p>
    </div>
  `,
  data() {
    return {
      username: '',
      email: '',
      password: ''
    };
  },
  methods: {
    register() {
            // Make an Axios POST request to Flask API for registration
            axios.post('/api/register', {
              username: this.username,
              email: this.email,
              password: this.password,
            })
            .then(response => {
              console.log(response.data.message);
              alert("account is created");
              this.$router.push('/login');

              // Redirect or perform other actions as needed
            })
            .catch(error => {
              console.error('Registration failed:', error.response.data.message);
            });
  }
}
};
axios.defaults.baseURL = 'http://127.0.0.1:5000';
const routes = [
  { path: '/login', component: LoginComponent },
  { path: '/register', component: RegistrationComponent },
  { path: '/', redirect: '/login' }, // Default home page redirects to /login
  {path: '/dashBoard',     beforeEnter(to, from, next) {
    window.location.replace("http://127.0.0.1:5000/dashBoard")
}},
];

const router = new VueRouter({
  routes,
});

new Vue({
  el: '#app',
  router,
});

  
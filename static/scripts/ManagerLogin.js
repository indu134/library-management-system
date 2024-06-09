const routes = [
    {path: '/dashBoard',     beforeEnter(to, from, next) {
        window.location.replace("http://127.0.0.1:5000/managerDashBoard")
    }},
];

const router = new  VueRouter({
    routes
});


new Vue({
    el: '#app',
    router,
    data: {
        username: '',
        password: ''
    },
    methods: {
        login() {
            // Add your login logic here
            const loginData = {
                username: this.username,
                password: this.password
            };

            // Make an API call to the server for authentication using Axios
            axios.post('/api/managerlogin', loginData)
                .then(response => {
                    // Handle the successful login response
                    const token = response.data.token;

                    // Save the token to local storage
                    localStorage.setItem('managertoken', token);
                    localStorage.setItem('manager',this.username);

                    console.log('Login successful. Token:', token);
                    this.$router.push("/dashBoard")
                    // You may redirect to a new page or perform other actions here
                })
                .catch(error => {
                    // Handle login error
                    console.error('Login failed:', error.response.data.message);
                    // Display an error message or take appropriate action
                });
        }
    }
});


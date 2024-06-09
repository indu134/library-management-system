// Vue component for displaying books
// Vue component for displaying books with Bootstrap cards

const UserNavComponent={
    template:`
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav"
            aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav">
            <li class="nav-item">
                <router-link to="/" class="nav-link">Home</router-link>
            </li>
            <li class="nav-item">
                <router-link to="/book-requests" class="nav-link">Requested Books</router-link>
            </li>
            <li class="nav-item">
                <router-link to="/accepted-books" class="nav-link">Issued Books</router-link>
            </li>
            <li class="nav-item">
                <router-link to="/rejected-books" class="nav-link">Rejected Books</router-link>
            </li>
            
            <li class="nav-item">
                <router-link to="/revoked-books" class="nav-link">Revoked Books</router-link>
            </li>
            <li class="nav-item">
            <router-link to="/manager-overview" class="nav-link">Stats</router-link>
        </li>
        </ul>
        <ul class="navbar-nav ml-auto">
            <li class="nav-item">
                <p class="nav-link">Welcome, {{ username }}</p>
             
            </li>
            <li class="nav-item">
                <button @click="logout" class="btn btn-outline-danger">Logout</button>
            </li>
        </ul>
    </div>
</nav>
    `,
    data(){
        return {
            username:'',
        };
    },
    mounted() {
        this.username = localStorage.getItem('manager');
        console.log(this.username);
      },
      methods: {
        logout() {
          localStorage.removeItem('managertoken');
          localStorage.removeItem('manager');
          this.$router.push('/login');
        }
      }

};
const BooksComponent = {
    template: `
        <div>
            <div v-for="(section, index) in sections" :key="index">
                <h3 class="mb-3">{{ section.name }}</h3>
                <div class="card-deck">
                    <div v-for="book in section.books" :key="book.id" class="card mb-4" style="max-width: 250px;">
                        <img :src="book.image" class="card-img-top img-fluid" alt="Book Image">
                        <div class="card-body">
                            <h5 class="card-title">{{ book.title }}</h5>
                            <p class="card-text">Author: {{ book.author }}</p>
                            <p class="card-text">Price: {{ book.price.toFixed(2) }}</p>
                            <button @click="deleteBook(book.id)" class="btn btn-danger">Delete</button>
                            <router-link :to="{ name: 'edit', params: { id: book.id }}" class="btn btn-primary">Edit</router-link>
                            <button @click="readBook(book.id)" class="btn btn-secondary">Read Book</button>
                        </div>
                    </div>
                </div>
                <div class="text-center">
                    <router-link :to="{ name: 'add', params: { sid: section.id }}" class="btn btn-success">Add Book</router-link>
                    <button @click="deleteSection(section.id)" class="btn btn-danger">Delete Section</button>
                </div>
                <hr> <!-- Add a horizontal line after each section -->
            </div>
            <!-- Add a border between Add Section button and sections -->
            <hr>
            <!-- Add Section Button at the bottom -->
            <div class="fixed-bottom bg-light p-3 text-center">
                <router-link to="/add-section" class="btn btn-primary btn-sm">Add Section</router-link> <!-- Reduced size button -->
            </div>
        </div>
    `,

    data() {
        return {
            sections: []
        };
    },
    mounted() {
        this.fetchSections();
    },
    methods: {
        fetchSections() {
            axios.get('/api/sections') // Replace with your actual API endpoint
                .then(response => {
                    this.sections = response.data.sections;
                })
                .catch(error => {
                    console.error('Error fetching sections:', error);
                });
        },
        deleteBook(bookId) {
            axios.delete(`/api/books/${bookId}`) // Replace with your actual API endpoint
                .then(response => {
                    this.fetchSections();
                })
                .catch(error => {
                    console.error('Error deleting book:', error);
                });
        },
        deleteSection(sectionId) {
            axios.delete(`/api/sections/${sectionId}`) // Replace with your actual API endpoint
                .then(response => {
                    this.fetchSections();
                })
                .catch(error => {
                    console.error('Error deleting section:', error);
                });
        },
        readBook(bookId) {
            // Navigate to the route where you want to display the book details
            // You can pass the book ID as a route parameter
            this.$router.push({ path: `/pdf-read/${bookId}` });
        }
    }
};


const AddSectionComponent = {
    template: `
        <div class="container mt-5">
            <h2 class="text-center mb-4">Add Section</h2>
            <div class="form-container border p-4">
                <form @submit.prevent="submitForm">
                    <div class="form-group">
                        <label for="sectionName">Section Name:</label>
                        <input v-model="sectionName" id="sectionName" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Add Section</button>
                </form>
            </div>
        </div>
    `,
    data() {
        return {
            sectionName: ''
        };
    },
    methods: {
        submitForm() {
            axios.post('/api/add-section', { name: this.sectionName })
                .then(response => {
                    console.log(response.data.message);
                    // Optionally, navigate to another route after successful addition
                    this.$router.push('/');
                })
                .catch(error => {
                    console.error('Error adding section:', error);
                });
        }
    }
};




// Vue component for adding/editing books
const BookFormComponent = {
    template: `
        <div class="container mt-5">
            <h2 class="text-center mb-4">{{ formTitle }}</h2>
            <div class="form-container border p-4">
                <form @submit.prevent="submitForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="section">Section:</label>
                        <input v-model="book.section" id="section" class="form-control" required :readonly="P1 === 'readonly'">
                    </div>
                    <div class="form-group">
                        <label for="title">Title:</label>
                        <input v-model="book.title" id="title" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label for="author">Author:</label>
                        <input v-model="book.author" id="author" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label for="price">Price:</label>
                        <input v-model="book.price" type="number" step="0.01" id="price" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label for="image">Image:</label>
                        <input type="file" @change="handleImageUpload" id="image" class="form-control-file" accept=".jpg,.png,.jpeg,.webp">
                    </div>
                    <div class="form-group">
                        <label for="ebook">Ebook:</label>
                        <input type="file" @change="handleEbookUpload" id="ebook" class="form-control-file" accept=".pdf">
                    </div>
                </form>
            </div>
            <div class="text-center mt-3">
                <button @click="submitForm" class="btn btn-primary mb-2">Submit</button>
                <br>
                <router-link to="/" class="btn btn-secondary">Back to Books</router-link>
            </div>
        </div>
    `,
    data() {
        return {
            book: {
                title: '',
                author: '',
                price: 0,
                section: '',
                image: null,
                ebook: null
            },
            formTitle: 'Add New Book',
            P1: 'readonly'
        };
    },
    mounted() {
        // If an ID parameter is provided, fetch book data for editing
        if (this.$route.params.id) {
            this.formTitle = 'Edit Book';
            this.P1 = '';
            axios.get(`/api/books/${this.$route.params.id}`)
                .then(response => {
                    this.book = response.data.book;
                })
                .catch(error => {
                    console.error('Error fetching book data:', error);
                });
        }
        if (this.$route.params.sid) {
            axios.get(`/api/sections/${this.$route.params.sid}`)
                .then(response => {
                    this.book.section = response.data.section.name;
                })
                .catch(error => {
                    console.error('Error fetching section data:', error);
                });
        }
    },
    methods: {
        submitForm() {
            const formData = new FormData();
            formData.append('title', this.book.title);
            formData.append('author', this.book.author);
            formData.append('price', this.book.price);
            formData.append('photo', this.book.image);
            formData.append('ebook', this.book.ebook);
            formData.append('section',this.book.section);

            if (this.$route.params.id) {
                // If editing, send a PUT request
                axios.put(`/api/books/${this.$route.params.id}`, formData,{
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                })
                    .then(response => {
                        // Handle success (e.g., redirect to books list)
                        this.$router.push('/');
                    })
                    .catch(error => {
                        console.error('Error updating book:', error);
                    });
            } else {
                // If adding, send a POST request
                axios.post('/api/books', formData,{
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                })
                    .then(response => {
                        // Handle success (e.g., redirect to books list)
                        this.$router.push('/');
                    })
                    .catch(error => {
                        console.error('Error adding new book:', error);
                    });
            }
        },
        handleImageUpload(event) {
            this.book.image = event.target.files[0];
        },
        handleEbookUpload(event) {
            this.book.ebook = event.target.files[0];
        }
    }
};



// Vue component for displaying book requests
const BookRequestsComponent = {
    template: `
        <div>
            <h2 class="mb-4">Book Requests</h2>
            <div class="card-deck">
                <div v-for="request in bookRequests" v-if="request.status === 'pending'" :key="request.id" class="card mb-4" style="max-width: 250px;">
                    <img :src="request.image" class="card-img-top img-fluid" alt="Book Image">
                    <div class="card-body">
                        <h5 class="card-title">{{ request.title }}</h5>
                        <p class="card-text">Requested User: {{ request.user }}</p>
                        <p class="card-text">Requested User Book Limit: {{ request.userbooklimit }}</p>
                        <p class="card-text">Author: {{ request.author }}</p>
                        <p class="card-text">Status: {{ request.status }}</p>
                        <button v-if="request.status === 'pending'" @click="handleAction('accept', request.id)" class="btn btn-success">Accept</button>
                        <button v-if="request.status === 'pending'" @click="handleAction('reject', request.id)" class="btn btn-danger">Reject</button>
                    </div>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            bookRequests: []
        };
    },
    mounted() {
        this.fetchBookRequests();
    },
    methods: {
        fetchBookRequests() {
            axios.get('/api/book-requests') // Replace with your actual API endpoint
                .then(response => {
                    this.bookRequests = response.data.book_requests;
                })
                .catch(error => {
                    console.error('Error fetching book requests:', error);
                });
        },
        handleAction(action, requestId) {
            // Implement the logic to accept or reject the book request
            axios.post('/api/book-requests', { 'book_id': requestId, 'action':action })
                .then(response => {
                    // Handle success (e.g., update the UI)
                    console.log(response.data.message);
                    this.fetchBookRequests();  // Refresh the list after action
                })
                .catch(error => {
                    console.error('Error handling book request:', error);
                });
        }
    }
};

// Vue component for displaying accepted books
const AcceptedBooksComponent = {
    template: `
        <div>
            <h2 class="mb-4">Accepted Books</h2>
            <div class="card-deck">
                <div v-for="book in acceptedBooks" :key="book.id" class="card mb-4" style="max-width: 250px;">
                    <img :src="book.image" class="card-img-top img-fluid" alt="Book Image">
                    <div class="card-body">
                        <h5 class="card-title">{{ book.title }}</h5>
                        <p class="card-text">Requested User: {{ book.user }}</p>
                        <p class="card-text">Requested User Book Limit: {{ book.userbooklimit }}</p>
                        <p class="card-text">Author: {{ book.author }}</p>
                        <p class="card-text">Status: {{ book.status }}</p>
                        <p class="card-text">Expires: {{ book.expires }}</p>
                        <button @click="revokeBook(book.id)" class="btn btn-warning">Revoke</button>
                    </div>
                </div>
            </div>
        </div>
    `,

    data() {
        return {
            acceptedBooks: []
        };
    },
    mounted() {
        this.fetchAcceptedBooks();
    },
    methods: {
        fetchAcceptedBooks() {
            axios.get('/api/accepted-books') // Replace with your actual API endpoint
                .then(response => {
                    this.acceptedBooks = response.data.accepted_books;
                })
                .catch(error => {
                    console.error('Error fetching accepted books:', error);
                });
        },
        revokeBook(bookId) {
            // Implement the logic to revoke the accepted book
            axios.post('/api/revoke-book', { book_id: bookId })
                .then(response => {
                    // Handle success (e.g., update the UI)
                    console.log(response.data.message);
                    this.fetchAcceptedBooks();  // Refresh the list after revoking
                })
                .catch(error => {
                    console.error('Error revoking book:', error);
                });
        }
    }
};
// Vue component for manager to view rejected books
const RejectedBooksComponent = {
    template: `
        <div>
            <h2 class="mb-4">Rejected Books</h2>
            <div class="card-deck">
                <div v-for="book in rejectedBooks" :key="book.id" class="card mb-4" style="max-width: 250px;">
                    <img :src="book.image" class="card-img-top img-fluid" alt="Book Image">
                    <div class="card-body">
                        <h5 class="card-title">{{ book.title }}</h5>
                        <p class="card-text">Author: {{ book.author }}</p>
                        <p class="card-text">Status: {{ book.status }}</p>
                        <p class="card-text">Requested User: {{ book.user }}</p>
                        <p class="card-text">Requested User Book Limit: {{ book.userbooklimit }}</p>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            rejectedBooks: []
        };
    },
    mounted() {
        this.fetchRejectedBooks();
    },
    methods: {
        fetchRejectedBooks() {
            axios.get('/api/manager/rejected-books') // Replace with your actual API endpoint
                .then(response => {
                    this.rejectedBooks = response.data.rejected_books;
                })
                .catch(error => {
                    console.error('Error fetching rejected books:', error);
                });
        }
    }
};
// Vue component for manager to view revoked books
const RevokedBooksComponent = {
    template: `
        <div>
            <h2 class="mb-4">Revoked Books</h2>
            <div class="card-deck">
                <div v-for="book in revokedBooks" :key="book.id" class="card mb-4" style="max-width: 250px;">
                    <img :src="book.image" class="card-img-top img-fluid" alt="Book Image">
                    <div class="card-body">
                        <h5 class="card-title">{{ book.title }}</h5>
                        <p class="card-text">Author: {{ book.author }}</p>
                        <p class="card-text">Status: {{ book.status }}</p>
                        <p class="card-text">Requested User: {{ book.user }}</p>
                        <p class="card-text">Requested User Book Limit: {{ book.userbooklimit }}</p>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            revokedBooks: []
        };
    },
    mounted() {
        this.fetchRevokedBooks();
    },
    methods: {
        fetchRevokedBooks() {
            axios.get('/api/manager/revoked-books') // Replace with your actual API endpoint
                .then(response => {
                    this.revokedBooks = response.data.revoked_books;
                })
                .catch(error => {
                    console.error('Error fetching revoked books:', error);
                });
        }
    }
};

const ManagerStatisticsComponent = {
    template: `
        <div>
            <h2>Section Statistics</h2>
            <div>
                <canvas id="bookDistributionChart" width="300" height="200"></canvas>
            </div>

            <h2>User Reading Statistics</h2>
            <div>
                <canvas id="userReadingStatusChart" width="300" height="200"></canvas>
            </div>

            <h2>Request Status Statistics</h2>
            <div>
                <canvas id="requestStatusChart" width="300" height="200"></canvas>
            </div>

            <h2>Completed Book Statistics</h2>
            <div>
                <canvas id="completedBookDistributionChart" width="300" height="200"></canvas>
            </div>
        </div>
    `,
    data() {
        return {
            sectionDistribution: {},
            userReadingStatus: {},
            requestStatuses: {},
            completedBookDistribution: {}
        };
    },
    mounted() {
        this.fetchData();
    },
    methods: {
        fetchData() {
            axios.all([
                axios.get('/api/manager/book-distribution'),
                axios.get('/api/manager/user-reading-status'),
                axios.get('/api/manager/request-status'),
                axios.get('/api/manager/completed-book-distribution')
            ]).then(axios.spread((bookDistributionRes, userReadingStatusRes, requestStatusRes, completedBookDistributionRes) => {
                this.sectionDistribution = bookDistributionRes.data;
                this.userReadingStatus = userReadingStatusRes.data;
                this.requestStatuses = requestStatusRes.data;
                this.completedBookDistribution = completedBookDistributionRes.data;
                this.renderBookDistributionChart();
                this.renderUserReadingStatusChart();
                this.renderRequestStatusChart();
                this.renderCompletedBookDistributionChart();
            })).catch(error => {
                console.error('Error fetching data:', error);
            });
        },
        renderBookDistributionChart() {
            new Chart(document.getElementById("bookDistributionChart"), {
                type: 'bar',
                data: {
                    labels: Object.keys(this.sectionDistribution),
                    datasets: [{
                        label: 'Book Distribution',
                        data: Object.values(this.sectionDistribution),
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    maintainAspectRatio: false
                }
            });
        },
        renderUserReadingStatusChart() {
            new Chart(document.getElementById("userReadingStatusChart"), {
                type: 'pie',
                data: {
                    labels: Object.keys(this.userReadingStatus),
                    datasets: [{
                        data: Object.values(this.userReadingStatus),
                        backgroundColor: ['rgba(255, 99, 132, 0.5)', 'rgba(54, 162, 235, 0.5)', 'rgba(255, 206, 86, 0.5)'],
                        borderColor: ['#FF6384', '#36A2EB'],
                        borderWidth: 1
                    }]
                },
                options: {
                    maintainAspectRatio: false
                }
            });
        },
        renderRequestStatusChart() {
            new Chart(document.getElementById("requestStatusChart"), {
                type: 'doughnut',
                data: {
                    labels: Object.keys(this.requestStatuses),
                    datasets: [{
                        data: Object.values(this.requestStatuses),
                        backgroundColor: ['rgba(255, 99, 132, 0.5)', 'rgba(54, 162, 235, 0.5)', 'rgba(255, 206, 86, 0.5)'],
                        borderColor: ['#FF6384', '#36A2EB', '#FFCE56'],
                        borderWidth: 1
                    }]
                },
                options: {
                    maintainAspectRatio: false
                }
            });
        },
        renderCompletedBookDistributionChart() {
            new Chart(document.getElementById("completedBookDistributionChart"), {
                type: 'line',
                data: {
                    labels: Object.keys(this.completedBookDistribution),
                    datasets: [{
                        label: 'Completed Books',
                        data: Object.values(this.completedBookDistribution),
                        fill: false,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    maintainAspectRatio: false
                }
            });
        }
    }
};






axios.defaults.baseURL = 'http://127.0.0.1:5000';

axios.interceptors.request.use(
    config => {
        const token = localStorage.getItem('managertoken');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);
// Vue Router setup
const routes = [
    { path: '/', component: BooksComponent },
    { path: '/add/:sid',name : 'add', component: BookFormComponent },
    { path: '/edit/:id', name: 'edit', component: BookFormComponent },
    { path: '/book-requests', component: BookRequestsComponent },
    { path: '/accepted-books', component: AcceptedBooksComponent },
    {path: '/rejected-books',component: RejectedBooksComponent},
    {path : '/revoked-books',component: RevokedBooksComponent},
    {path:'/add-section',component: AddSectionComponent},
    {path:'/manager-overview',component:ManagerStatisticsComponent},
    {
        path: '/pdf-read/:pdfName',
        beforeEnter(to, from, next) {
          // Open the PDF preview URL in a new tab
         const token = localStorage.getItem('managertoken')
          window.open(`http://127.0.0.1:5000/manager/${token}/${to.params.pdfName}`, '_blank');
          
        }
      },
    {path: '/login',     beforeEnter(to, from, next) {
        window.location.replace("http://127.0.0.1:5000/managerLogin")
    }},
];

const router = new  VueRouter({
    routes
});

// Vue app instance
new Vue({
    el: '#app',
    router,
    components: {
        'user-nav': UserNavComponent ,
    }
});

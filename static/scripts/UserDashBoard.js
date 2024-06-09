// Vue component for user dashboard
var UserNavComponent = Vue.extend({
    template: `
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
                <router-link to="/requested-books" class="nav-link">Requested Books</router-link>
            </li>
            <li class="nav-item">
                <router-link to="/issued-books" class="nav-link">Issued Books</router-link>
            </li>
            <li class="nav-item">
                <router-link to="/rejected-books" class="nav-link">Rejected Books</router-link>
            </li>
            <li class="nav-item">
                <router-link to="/revoked-books" class="nav-link">Revoked Books</router-link>
            </li>
            <li class="nav-item">
                <router-link to="/completed-books" class="nav-link">Completed Books</router-link>
            </li>
        </ul>
        <ul class="navbar-nav ml-auto">
            <li class="nav-item">
                <p v-if="userDetails" class="nav-link">Welcome, {{ userDetails.username }}</p>
            </li>
            <li class="nav-item">
                <p v-if="userDetails" class="nav-link">Request Limit : {{ userDetails.maximum_book_requested }}</p>
            </li>
            <li class="nav-item">
                <p v-if="userDetails" class="nav-link">Issued Limit : {{ userDetails.maximum_book_issued }}</p>
            </li>
            <li class="nav-item">
                <button @click="logout" class="btn btn-outline-danger">Logout</button>
            </li>
        </ul>
    </div>
</nav>
    `,
    data() {
        return {
            userDetails: null,
        };
    },
    mounted() {
        this.fetchUserData();
    },
    methods: {
        fetchUserData() {
            axios.get('/api/userdetails')
                .then(response => {
                    this.userDetails = response.data;
                })
                .catch(error => {
                    console.error('Error fetching user data:', error);
                });
        },
        logout() {
            localStorage.removeItem('token');
            this.$router.push('/login');
        },
        updateUserData: function(){
            this.fetchUserData();
        }
       
    },
});



const UserDashboardComponent = {
    template: `
        <div>
        <div class="col-md-6"></div> 
        <div class="col-md-6 d-flex justify-content-end">
            <input type="text" v-model="searchQuery" @input="searchBooks" placeholder="Search...">
        </div>
            <h2 class="mb-4">All Available Books</h2>
            <div class="card-deck">
                <div v-for="book in filteredBooks" :key="book.id" class="card mb-4" style="max-width: 200px;">
                    <img :src="book.image" class="card-img-top img-fluid" alt="Book Image">
                    <div class="card-body">
                        <h5 class="card-title">{{ book.title }}</h5>
                        <p class="card-text">Author: {{ book.author }}</p>
                        <p class="card-text">Section: {{ book.section }}</p>
                        <p class="card-text">Price: {{ book.price.toFixed(2) }}</p>
                        <p class="card-text">Rating: {{ book.rating }}/5 By {{book.number_of_users}} Readers</p> 
                        <div class="d-flex justify-content-between">
                            <button @click="requestBook(book.id)" class="btn btn-primary mr-2">Request</button>
                            <button @click="previewBook(book.id)" class="btn btn-success">Preview</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            books: [],
            searchQuery: ''
        };
    },
    mounted() {
        this.fetchBooks();
        
    },
    computed: {
        filteredBooks() {
            // Filter books based on searchQuery
            return this.books.filter(book =>
                book.title.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
                book.author.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
                book.section.toLowerCase().includes(this.searchQuery.toLowerCase())
            );
        }
    },
    methods: {
        fetchBooks() {
            axios.get('/api/all-books') // Include JWT token in request headers
                .then(response => {
                    this.books = response.data.books;
                })
                .catch(error => {
                    console.error('Error fetching books:', error);
                });
        },
        requestBook(bookId) {
            // Implement logic to request a book
            axios.post('/api/request-book', { book_id: bookId })
                .then(response => {
                    console.log(response.data.message);
                    // Optionally update UI to indicate success
                    vm.$refs.userdata.updateUserData();
                    this.$router.push({ path: '/requested-books' });
                })
                .catch(error => {
                    console.error('Error requesting book:', error);
                });
        },
        previewBook(ebook) {
            // Navigate to the PDF preview route with the ebook URL as a parameter
            this.$router.push({ path: `/pdf-preview/${ebook}` });
        },
        searchBooks() {
            // This method is automatically called whenever the searchQuery changes
            // No need to explicitly call it
        }
    }
};


  
  

// Vue component for displaying requested books
// Vue component for displaying requested books
const RequestedBooksComponent = {
    template: `
        <div>
            <h2 class="mb-4">Requested Books</h2>
            <div class="card-deck">
                <div v-for="book in requestedBooks" :key="book.id" class="card mb-4" style="max-width: 250px;">
                    <img :src="book.image" class="card-img-top img-fluid" alt="Book Image">
                    <div class="card-body">
                        <h5 class="card-title">{{ book.title }}</h5>
                        <p class="card-text">Author: {{ book.author }}</p>
                        <p class="card-text">Status: {{ book.status }}</p>
                        <button v-if="book.status === 'pending'" @click="deleteBookRequest(book.id)" class="btn btn-danger">Delete Request</button>
                        <button v-else disabled class="btn btn-danger" title="Cannot delete this request">Delete Request</button>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            requestedBooks: []
        };
    },
    mounted() {
        this.fetchRequestedBooks();
    },
    methods: {
        fetchRequestedBooks() {
            axios.get('/api/requested-books') // Replace with your actual API endpoint
                .then(response => {
                    this.requestedBooks = response.data.requested_books;
                })
                .catch(error => {
                    console.error('Error fetching requested books:', error);
                });
        },
        deleteBookRequest(bookId) {
            axios.post('/api/delete-request', { book_id: bookId }) // Replace with your actual API endpoint
                .then(response => {
                    console.log(response.data.message);
                    this.fetchRequestedBooks(); // Refresh the list after deleting
                    vm.$refs.userdata.updateUserData();
                })
                .catch(error => {
                    console.error('Error deleting book request:', error);
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
                <div v-for="book in acceptedBooks" :key="book.id" class="card mb-3" style="max-width: 250px;">
                    <img :src="book.image" class="card-img-top img-fluid" alt="Book Image">
                    <div class="card-body">
                        <h5 class="card-title">{{ book.title }}</h5>
                        <p class="card-text">Author: {{ book.author }}</p>
                        <p class="card-text">Status: {{ book.status }}</p>
                        <p class="card-text">Expires: {{ book.expires }}</p>
                        <button @click="readBook(book.id)" class="btn btn-primary">Read Book</button>
                        <div v-if="book.status === 'accepted'" class="mt-3">
                        <select v-model="book.ratingInput" class="form-control mb-2">
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                        <option value="5">5</option>
                    </select>
                    <button @click="submitRating(book.id, book.ratingInput)" class="btn btn-primary">Submit Rating</button>
                            <button @click="markAsCompleted(book.id)" v-if="book.reading_status !== 'completed'" class="btn btn-success">Mark as Completed</button>
                            <p v-else>Marked as Completed</p>
                            <button @click="returnBook(book.id)" class="btn btn-danger">Return Book</button>
                        </div>
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
            axios.get('/api/user/accepted-books') // Replace with your actual API endpoint
                .then(response => {
                    this.acceptedBooks = response.data.accepted_books;
                })
                .catch(error => {
                    console.error('Error fetching accepted books:', error);
                });
        },
        readBook(bookId) {
            // Navigate to the route where you want to display the book details
            // You can pass the book ID as a route parameter
            this.$router.push({ path: `/pdf-read/${bookId}` });
        },
        markAsCompleted(bookId) {
            // Implement logic to mark the book as completed
            axios.post('/api/mark-as-completed', { book_id: bookId })
                .then(response => {
                    console.log(response.data.message);
                    // Optionally update UI to indicate success
                    // You may want to refetch the accepted books after marking as completed
                    this.fetchAcceptedBooks();
                })
                .catch(error => {
                    console.error('Error marking as completed:', error);
                });
        },
        submitRating(bookId, rating) {
            // Implement logic to submit the rating to the server
            axios.post('/api/submit-rating', { book_id: bookId, rating: rating })
                .then(response => {
                    console.log(response.data.message);
                    // Optionally update UI to indicate success

                })
                .catch(error => {
                    console.error('Error submitting rating:', error);
                });
        },
        returnBook(bookId) {
            // Implement logic to return the book
            axios.post('/api/return-book', { book_id: bookId })
                .then(response => {
                    console.log(response.data.message);
                    // Optionally update UI to indicate success
                    this.fetchAcceptedBooks();
                    vm.$refs.userdata.updateUserData(); // Refresh the list after returning the book
                })
                .catch(error => {
                    console.error('Error returning book:', error);
                });
        }
    }
};



// Vue component for displaying revoked books
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
            axios.get('/api/user/revoked-books') // Replace with your actual API endpoint
                .then(response => {
                    this.revokedBooks = response.data.revoked_books;
                })
                .catch(error => {
                    console.error('Error fetching revoked books:', error);
                });
        }
    }
};


// Vue component for displaying rejected books
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
            axios.get('/api/user/rejected-books') // Replace with your actual API endpoint
                .then(response => {
                    this.rejectedBooks = response.data.rejected_books;
                })
                .catch(error => {
                    console.error('Error fetching rejected books:', error);
                });
        }
    }
};

const CompletedBooksComponent = {
    template: `
        <div>
            <h2 class="mb-4">Completed Books</h2>
            <div class="card-deck">
                <div v-for="book in completedBooks" :key="book.id" class="card mb-3" style="max-width: 250px;">
                    <img :src="book.image" class="card-img-top img-fluid" alt="Book Image">
                    <div class="card-body">
                        <h5 class="card-title">{{ book.title }}</h5>
                        <p class="card-text">Author: {{ book.author }}</p>
                        <p class="card-text">Status: {{ book.reading_status }}</p>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            completedBooks: []
        };
    },
    mounted() {
        this.fetchCompletedBooks();
    },
    methods: {
        fetchCompletedBooks() {
            axios.get('/api/user/completed-books') // Replace with your actual API endpoint
                .then(response => {
                    this.completedBooks = response.data.completed_books;
                })
                .catch(error => {
                    console.error('Error fetching completed books:', error);
                });
        },
    }
};











axios.defaults.baseURL = 'http://127.0.0.1:5000';

axios.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token');
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
  { path: '/', component: UserDashboardComponent },
  {path:'/requested-books',component: RequestedBooksComponent},
  {path:'/issued-books',component: AcceptedBooksComponent},
  {path:'/rejected-books',component: RejectedBooksComponent},
  {path:'/revoked-books',component:RevokedBooksComponent},
  {path:'/completed-books',component:CompletedBooksComponent},
  {
    path: '/pdf-preview/:pdfName',
    beforeEnter(to, from, next) {
      // Open the PDF preview URL in a new tab
      window.open(`http://127.0.0.1:5000/${to.params.pdfName}`, '_blank');
      
    }
  },
  {
    path: '/pdf-read/:pdfName',
    beforeEnter(to, from, next) {
      // Open the PDF preview URL in a new tab
     const token = localStorage.getItem('token')
      window.open(`http://127.0.0.1:5000/user/${token}/${to.params.pdfName}`, '_blank');
      
    }
  },
  {path: '/login',     beforeEnter(to, from, next) {
    window.location.replace("http://127.0.0.1:5000/")
}},
];

const router = new VueRouter({
  routes
});


// Vue app instance
var vm = new Vue({
    el: '#app',
    router,
    components: {
        'user-nav': UserNavComponent ,
    }

  });


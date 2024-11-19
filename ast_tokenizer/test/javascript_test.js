/**
 * Yes this was generated by an LLM
 * But its just for testing
 */ 

// Global variables
let counter = 0;
const greeting = "Hello, World!";

// Regular Function Declaration
function incrementCounter() {
    counter++;
    console.log("Counter incremented:", counter);
}

// Arrow Function
const decrementCounter = () => {
    counter--;
    console.log("Counter decremented:", counter);
};

// Function Expression assigned to a variable
const multiply = function(a, b) {
    return a * b;
};

// Global loop
for (let i = 0; i < 5; i++) {
    console.log("Loop iteration:", i);
}

// Conditional statement
if (counter === 0) {
    console.log("Counter is at zero.");
} else {
    console.log("Counter is non-zero.");
}

// Ternary operator example
const statusMessage = counter > 0 ? "Counter is positive." : "Counter is zero or negative.";
console.log(statusMessage);

// Calling the functions
incrementCounter();
decrementCounter();

// Using the function expression
const result = multiply(4, 5);
console.log("Multiplication result:", result);

// Global object with method
const person = {
    name: "John",
    age: 30,
    greet: function() {
        console.log(`Hello, my name is ${this.name} and I am ${this.age} years old.`);
    },
    incrementAge: function() {

// Test utility for demonstrating different JavaScript patterns
// Global utility functions
const globalHelper = () => {
    console.log("Global helper function");
};

/**
 * Main application class
 * Demonstrates various JavaScript features
 */
class Application {
    // Class fields
    static VERSION = '1.0.0';
    #privateField = 'secret';
    
    constructor(config = {}) {
        this.name = config.name || 'DefaultApp';
        this.initialized = false;
    }

    // Regular method
    initialize() {
        this.initialized = true;
        return this.#initializeInternal();
    }

    // Private method
    #initializeInternal() {
        return {
            status: 'success',
            timestamp: Date.now()
        };
    }

    // Static method
    static getInfo() {
        return {
            version: this.VERSION,
            buildDate: new Date()
        };
    }

    // Async method
    async fetchData() {
        try {
            const response = await fetch('https://api.example.com/data');
            return await response.json();
        } catch (error) {
            console.error('Error fetching data:', error);
            return null;
        }
    }

    // Generator method
    *generateSequence() {
        yield 1;
        yield 2;
        yield 3;
    }
}

// Different function declaration types
// Regular function declaration
function processData(data, options = {}) {
    const { format = 'json', validate = true } = options;
    
    if (validate) {
        validateData(data);
    }

    return format === 'json' ? JSON.stringify(data) : data;
}

// Function expression
const validateData = function(data) {
    if (!data) {
        throw new Error('Data is required');
    }
    return true;
};

// Arrow function with destructuring
const formatResponse = ({ data, metadata = {} }) => {
    return {
        ...data,
        timestamp: metadata.timestamp || Date.now(),
        formatted: true
    };
};

// Immediately Invoked Function Expression (IIFE)
const config = (() => {
    const defaultConfig = {
        environment: 'development',
        debug: true
    };

    return {
        get: (key) => defaultConfig[key],
        set: (key, value) => {
            defaultConfig[key] = value;
        }
    };
})();

// Class expression
const DataProcessor = class {
    constructor(options = {}) {
        this.options = options;
    }

    process(data) {
        return this.#transform(data);
    }

    #transform(data) {
        // Private method implementation
        return data.map(item => ({
            ...item,
            processed: true
        }));
    }
};

// Higher-order function
function createMiddleware(options = {}) {
    const { logger = console.log } = options;
    
    return function middleware(req, res, next) {
        logger(`Request received: ${req.url}`);
        next();
    };
}

// Async function with multiple parameters
async function fetchUserData(userId, { includeProfile = false, includePosts = false } = {}) {
    const user = await db.users.findById(userId);
    
    if (!user) {
        throw new Error('User not found');
    }

    const result = { user };

    if (includeProfile) {
        result.profile = await db.profiles.findByUserId(userId);
    }

    if (includePosts) {
        result.posts = await db.posts.findByAuthor(userId);
    }

    return result;
}

// Complex arrow function with default parameters and rest operator
const combineConfigs = (baseConfig = {}, ...overrides) => {
    return overrides.reduce((acc, config) => ({
        ...acc,
        ...config,
        nested: {
            ...acc.nested,
            ...config.nested
        }
    }), baseConfig);
};

// Factory function pattern
function createAPIClient({ baseURL, timeout = 5000, headers = {} }) {
    const defaultHeaders = {
        'Content-Type': 'application/json',
        ...headers
    };

    return {
        async get(endpoint) {
            // Implementation
            return fetch(`${baseURL}${endpoint}`, {
                headers: defaultHeaders,
                timeout
            });
        },
        
        async post(endpoint, data) {
            return fetch(`${baseURL}${endpoint}`, {
                method: 'POST',
                headers: defaultHeaders,
                timeout,
                body: JSON.stringify(data)
            });
        }
    };
}

// Event handling with closure
function createEventHandler(element, eventType) {
    let handlers = new Set();

    element.addEventListener(eventType, (event) => {
        handlers.forEach(handler => handler(event));
    });

    return {
        addHandler(handler) {
            handlers.add(handler);
        },
        removeHandler(handler) {
            handlers.delete(handler);
        },
        clearHandlers() {
            handlers.clear();
        }
    };
}

// Module pattern
const UserModule = (() => {
    // Private variables
    const users = new Map();
    let nextId = 1;

    // Private function
    function generateId() {
        return `user_${nextId++}`;
    }

    // Public interface
    return {
        addUser(userData) {
            const id = generateId();
            users.set(id, {
                id,
                ...userData,
                createdAt: new Date()
            });
            return id;
        },

        getUser(id) {
            return users.get(id);
        },

        updateUser(id, updates) {
            if (!users.has(id)) {
                throw new Error('User not found');
            }
            
            const user = users.get(id);
            users.set(id, {
                ...user,
                ...updates,
                updatedAt: new Date()
            });
            
            return users.get(id);
        }
    };
})();

// Export statement
export {
    Application,
    DataProcessor,
    createAPIClient,
    UserModule,
    processData,
    createEventHandler,
    combineConfigs
};
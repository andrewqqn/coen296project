import React, { useState, useEffect } from 'react';
import { auth, googleProvider } from './firebase'; // Import Firebase auth

const API_URL = '';

function App() {
    const [user, setUser] = useState(null);
    const [isAdmin, setIsAdmin] = useState(false);
    const [expenses, setExpenses] = useState([]);
    const [invoice, setInvoice] = useState(null);
    const [position, setPosition] = useState(''); // State for the position
    const [error, setError] = useState(null); // For error handling

    useEffect(() => {
        const unsubscribe = auth.onAuthStateChanged(async (user) => {
            if (user) {
                setUser(user);
                const tokenResult = await user.getIdTokenResult();
                setIsAdmin(tokenResult.claims.admin === true);
                fetchExpenses(user);
            } else {
                setUser(null);
                setIsAdmin(false);
                setExpenses([]);
            }
        });

        return () => unsubscribe();
    }, []);

    const fetchExpenses = async (user) => {
        try {
            const token = await user.getIdToken();
            const response = await fetch(`${API_URL}/expenses`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });
            if (!response.ok) {
                throw new Error(await response.text());
            }
            const data = await response.json();
            setExpenses(data);
        } catch (err) {
            setError(err.message);
        }
    };

    const handleFileChange = (e) => {
        setInvoice(e.target.files[0]);
    };

    const handlePositionChange = (e) => {
        setPosition(e.target.value);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);

        try {
            const token = await user.getIdToken();
            const formData = new FormData();
            formData.append('invoice', invoice);
            formData.append('position', position); // Add position to form data

            const response = await fetch(`${API_URL}/expenses`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });

            if (!response.ok) {
                throw new Error(await response.text());
            }

            fetchExpenses(user);
            // Clear form fields after submission
            setInvoice(null);
            setPosition('');
            e.target.reset(); // Reset the file input
        } catch (err) {
            setError(err.message);
        }
    };

    const handleStatusChange = async (id, status) => {
        setError(null);

        try {
            const token = await user.getIdToken();
            const response = await fetch(`${API_URL}/expenses/${id}`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({ status }),
            });

            if (!response.ok) {
                throw new Error(await response.text());
            }

            fetchExpenses(user);
        } catch (err) {
            setError(err.message);
        }
    };

    const signInWithGoogle = async () => {
        try {
            await auth.signInWithPopup(googleProvider);
        } catch (err) {
            setError(err.message);
        }
    };

    const signOut = async () => {
        await auth.signOut();
    };

    return (
        <div style={{ fontFamily: 'sans-serif', margin: '2em' }}>
            {error && <div style={{ color: 'red', marginBottom: '1em' }}>Error: {JSON.stringify(error)}</div>}

            {user ? (
                <div>
                    <h1>Expense Reimbursement</h1>
                    <p>Welcome, {user.displayName}! {isAdmin && <b>(Admin)</b>}</p>
                    <button onClick={signOut}>Sign Out</button>

                    <h2>Submit an Expense</h2>
                    <form onSubmit={handleSubmit} style={{ marginBottom: '2em', display: 'flex', flexDirection: 'column', maxWidth: '400px' }}>
                         <div style={{ marginBottom: '1em' }}>
                            <label htmlFor="position">Your Position:</label>
                            <input id="position" type="text" value={position} onChange={handlePositionChange} required style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}/>
                        </div>
                        <div style={{ marginBottom: '1em' }}>
                            <label htmlFor="invoice">Invoice File:</label>
                            <input id="invoice" type="file" onChange={handleFileChange} required />
                        </div>
                        <button type="submit">Submit</button>
                    </form>

                    <h2>Expense Requests</h2>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr>
                                <th style={tableHeaderStyle}>Employee</th>
                                <th style={tableHeaderStyle}>Position</th>
                                <th style={tableHeaderStyle}>Submitted</th>
                                <th style={tableHeaderStyle}>Invoice</th>
                                <th style={tableHeaderStyle}>Status</th>
                                <th style={tableHeaderStyle}>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {expenses.map((expense) => (
                                <tr key={expense.id}>
                                    <td style={tableCellStyle}>{expense.employee_name}</td>
                                    <td style={tableCellStyle}>{expense.position}</td>
                                    <td style={tableCellStyle}>{new Date(expense.submission_time).toLocaleString()}</td>
                                    <td style={tableCellStyle}>
                                        <a href={expense.invoice_url} target="_blank" rel="noopener noreferrer">
                                            View Invoice
                                        </a>
                                    </td>
                                    <td style={tableCellStyle}>{expense.status}</td>
                                    <td style={tableCellStyle}>
                                        {isAdmin && expense.status === 'pending' && (
                                            <div>
                                                <button onClick={() => handleStatusChange(expense.id, 'approved')} style={approveButtonStyle}>
                                                    Approve
                                                </button>
                                                <button onClick={() => handleStatusChange(expense.id, 'denied')} style={denyButtonStyle}>
                                                    Deny
                                                </button>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div>
                    <h1>Please Sign In</h1>
                    <button onClick={signInWithGoogle}>Sign in with Google</button>
                </div>
            )}
        </div>
    );
}

// Basic Styling
const tableHeaderStyle = {
    borderBottom: '2px solid #ddd',
    padding: '8px',
    textAlign: 'left',
};

const tableCellStyle = {
    borderBottom: '1px solid #ddd',
    padding: '8px',
};

const approveButtonStyle = {
    backgroundColor: '#4CAF50', // Green
    color: 'white',
    padding: '5px 10px',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
    marginRight: '5px',
};

const denyButtonStyle = {
    backgroundColor: '#f44336', // Red
    color: 'white',
    padding: '5px 10px',
    border: 'none',
    borderRadius: '3px',
    cursor: 'pointer',
};

export default App;

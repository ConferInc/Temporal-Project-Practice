import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../utils/api';
// We import jwt-decode safely; if it's not installed yet, this might fail build until npm install
import { jwtDecode } from 'jwt-decode';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for existing token on load
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const decoded = jwtDecode(token);
                // Extract email (sub) and role
                setUser({ email: decoded.sub, role: decoded.role });
            } catch (e) {
                console.error("Invalid token", e);
                localStorage.removeItem('token');
            }
        }
        setLoading(false);
    }, []);

    const login = async (email, password) => {
        // Current backend expects x-www-form-urlencoded for OAuth2 login endpoint
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });

        const { access_token } = response.data;
        localStorage.setItem('token', access_token);

        // Decode to get user info immediately
        const decoded = jwtDecode(access_token);
        const userObj = { email: decoded.sub, role: decoded.role };
        setUser(userObj);

        return userObj;
    };

    const register = async (email, password, role = 'applicant') => {
        // Backend API: POST /auth/register { email, password }
        // Note: Use role param if backend supports it in register payload, 
        // but currently backend assigns default 'applicant'. 
        // We strictly use the decoded token role as truth.
        const response = await api.post('/auth/register', { email, password });
        const { access_token } = response.data;

        localStorage.setItem('token', access_token);
        const decoded = jwtDecode(access_token);
        const userObj = { email: decoded.sub, role: decoded.role };
        setUser(userObj);
        return userObj;
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
        window.location.href = '/login';
    };

    return (
        <AuthContext.Provider value={{ user, login, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);

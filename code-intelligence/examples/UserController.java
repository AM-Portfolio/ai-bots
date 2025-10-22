package com.example.api.controllers;

import com.example.api.models.User;
import com.example.api.services.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import javax.validation.Valid;
import java.util.List;

/**
 * REST API Controller for User Management
 * 
 * Business Logic: Handles user CRUD operations and authentication
 * Technical: Spring Boot REST controller with validation and exception handling
 * API Contract: RESTful endpoints for user resources
 * Error Handling: Returns appropriate HTTP status codes
 */
@RestController
@RequestMapping("/api/v1/users")
@CrossOrigin(origins = "*", maxAge = 3600)
public class UserController {
    
    @Autowired
    private UserService userService;
    
    /**
     * Get user by ID
     * 
     * @param id User ID
     * @return User entity with 200 OK or 404 Not Found
     * @throws UserNotFoundException if user doesn't exist
     */
    @GetMapping("/{id}")
    public ResponseEntity<User> getUserById(@PathVariable Long id) {
        try {
            User user = userService.findById(id);
            return ResponseEntity.ok(user);
        } catch (UserNotFoundException e) {
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    
    /**
     * Create new user
     * 
     * @param user User data from request body
     * @return Created user with 201 Created
     * @throws ValidationException if input is invalid
     */
    @PostMapping
    public ResponseEntity<User> createUser(@Valid @RequestBody User user) {
        try {
            User createdUser = userService.save(user);
            return ResponseEntity.created(null).body(createdUser);
        } catch (DuplicateEmailException e) {
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * List all users with pagination
     * 
     * Performance: Supports pagination to handle large datasets
     * 
     * @param page Page number (default: 0)
     * @param size Page size (default: 20, max: 100)
     * @return List of users
     */
    @GetMapping
    public ResponseEntity<List<User>> listUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        
        if (size > 100) {
            size = 100; // Enforce max page size
        }
        
        List<User> users = userService.findAll(page, size);
        return ResponseEntity.ok(users);
    }
    
    /**
     * Delete user
     * 
     * Security: Requires admin role (handled by Spring Security)
     * 
     * @param id User ID
     * @return 204 No Content on success
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        userService.delete(id);
        return ResponseEntity.noContent().build();
    }
}

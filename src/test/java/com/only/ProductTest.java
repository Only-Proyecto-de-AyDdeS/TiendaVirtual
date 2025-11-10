package com.only;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class ProductTest {
    
    @Test
    public void testConstructorAndGetters() {
        Product product = new Product("Laptop", 999.99, 10);
        assertEquals("Laptop", product.getName());
        assertEquals(999.99, product.getPrice(), 0.001);
        assertEquals(10, product.getStock());
    }
    
    @Test
    public void testReduceStockSuccess() {
        Product product = new Product("Laptop", 999.99, 10);
        assertTrue(product.reduceStock(5));
        assertEquals(5, product.getStock());
    }
    
    @Test
    public void testReduceStockFailureNegativeQuantity() {
        Product product = new Product("Laptop", 999.99, 10);
        assertFalse(product.reduceStock(-1));
        assertEquals(10, product.getStock());
    }
    
    @Test
    public void testReduceStockFailureInsufficientStock() {
        Product product = new Product("Laptop", 999.99, 10);
        assertFalse(product.reduceStock(15));
        assertEquals(10, product.getStock());
    }
    
    @Test
    public void testCalculateDiscount() {
        Product product = new Product("Laptop", 1000.0, 10);
        assertEquals(900.0, product.calculateDiscount(10.0), 0.001);
    }
    
    @Test
    public void testCalculateDiscountInvalidNegative() {
        Product product = new Product("Laptop", 1000.0, 10);
        assertThrows(IllegalArgumentException.class, () -> {
            product.calculateDiscount(-10.0);
        });
    }
    
    @Test
    public void testCalculateDiscountInvalidOver100() {
        Product product = new Product("Laptop", 1000.0, 10);
        assertThrows(IllegalArgumentException.class, () -> {
            product.calculateDiscount(110.0);
        });
    }
}
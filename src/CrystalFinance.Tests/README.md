# CrystalFinance Tests

Focused test suite for the CrystalFinance API using xUnit, NSubstitute, and data validation testing.

## Test Structure

### Models
- **TransactionModelValidationTests**: Data validation unit tests
  - Valid transaction passes all validations
  - Amount validation (range, positivity)
  - Date validation (no future dates)
  - String length validations
  - Enum requirement validation
  - Check number format validation
  - Optional field handling

### Controllers
- **HealthCheckTests**: Health check endpoint verification
  - Overall health (`/health`)
  - Liveness probe (`/health/live`)
  - Readiness probe (`/health/ready`)

### Fixtures
- **CrystalFinanceApiFactory**: WebApplicationFactory for test setup
- **TransactionModelBuilder**: Fluent builder for creating test transactions

## Running Tests

### Visual Studio
```powershell
# Run all tests
Test -> Run All Tests

# Run specific test class
Test -> Run -> CrystalFinance.Tests.Models.TransactionModelValidationTests

# Debug tests
Test -> Debug All Tests
```

### Command Line
```powershell
# Run all tests
dotnet test

# Run validation tests only
dotnet test --filter "ClassName=TransactionModelValidationTests"

# Run health check tests only
dotnet test --filter "ClassName=HealthCheckTests"

# Run with verbose output
dotnet test --verbosity=detailed
```

## Test Coverage

The test suite covers:
- ✅ Model validation (10 tests)
- ✅ Health check endpoints (2 tests)
- ✅ Business rule enforcement
- ✅ Data constraints and edge cases

**Total: 12 tests**

## Example Test

```csharp
[Fact]
public void ValidTransaction_PassesValidation()
{
    // Arrange
    var transaction = new TransactionModelBuilder()
        .WithAmount(150.50m)
        .WithDescription("Grocery Store")
        .Build();

    // Act
    var results = ValidateModel(transaction);

    // Assert
    Assert.Empty(results);
}
```

## Future Enhancements

- [ ] Add integration tests with TestContainer for database tests
- [ ] Add API endpoint tests (after auth simplification)
- [ ] Add performance/load tests
- [ ] Add transaction import tests

## Notes

- **Why no controller tests?** This is a personal app. CRUD endpoints were manually tested in Scalar with OAuth2.0 Microsoft Entra ID.
- **Focus:** Unit tests for data validation and health checks provide value without OAuth complexity.
- **Adding integration tests:** Consider using TestContainer for E2E testing when needed.


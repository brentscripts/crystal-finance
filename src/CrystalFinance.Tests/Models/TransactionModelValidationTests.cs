using System.ComponentModel.DataAnnotations;
using CrystalFinance.Tests.Fixtures;
using CrystalFinanceLibrary.Models;
using Xunit;

namespace CrystalFinance.Tests.Models;

/// <summary>
/// Unit tests for TransactionModel validation attributes.
/// </summary>
public class TransactionModelValidationTests
{
    private static List<ValidationResult> ValidateModel(object model)
    {
        var context = new ValidationContext(model, null, null);
        var results = new List<ValidationResult>();
        Validator.TryValidateObject(model, context, results, true);
        return results;
    }

    [Fact]
    public void ValidTransaction_PassesValidation()
    {
        // Arrange
        var transaction = new TransactionModelBuilder().Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.Empty(results);
    }

    [Theory]
    [InlineData(0)]
    [InlineData(-1)]
    [InlineData(-999)]
    public void InvalidAmount_FailsValidation(decimal amount)
    {
        // Arrange
        var transaction = new TransactionModelBuilder()
            .WithAmount(amount)
            .Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.NotEmpty(results);
        Assert.Contains(results, r => r.ErrorMessage!.Contains("Amount must be between"));
    }

    [Fact]
    public void ExcessiveAmount_FailsValidation()
    {
        // Arrange
        var transaction = new TransactionModelBuilder()
            .WithAmount(1_000_000_000m)
            .Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.NotEmpty(results);
        Assert.Contains(results, r => r.ErrorMessage!.Contains("Amount must be between"));
    }

    [Fact]
    public void FutureTransactionDate_FailsValidation()
    {
        // Arrange
        var transaction = new TransactionModelBuilder()
            .WithTrxDate(DateTime.UtcNow.AddDays(1))
            .Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.NotEmpty(results);
        Assert.Contains(results, r => r.ErrorMessage!.Contains("cannot be in the future"));
    }

    [Fact]
    public void NullSource_FailsValidation()
    {
        // Arrange
        var transaction = new TransactionModelBuilder()
            .WithSource(null)
            .Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.NotEmpty(results);
        Assert.Contains(results, r => r.ErrorMessage!.Contains("source is required"));
    }

    [Fact]
    public void TooLongDescription_FailsValidation()
    {
        // Arrange
        var transaction = new TransactionModelBuilder()
            .WithDescription(new string('x', 256))
            .Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.NotEmpty(results);
        Assert.Contains(results, r => r.ErrorMessage!.Contains("cannot exceed 255"));
    }

    [Fact]
    public void InvalidCheckNumber_FailsValidation()
    {
        // Arrange
        var transaction = new TransactionModelBuilder()
            .WithCheckNumber("ABC123")  // Contains letters
            .Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.NotEmpty(results);
        Assert.Contains(results, r => r.ErrorMessage!.Contains("only digits"));
    }

    [Fact]
    public void ValidCheckNumber_PassesValidation()
    {
        // Arrange
        var transaction = new TransactionModelBuilder()
            .WithCheckNumber("123456")
            .Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.Empty(results);
    }

    [Fact]
    public void TooLongCategory_FailsValidation()
    {
        // Arrange
        var transaction = new TransactionModelBuilder()
            .WithCategory(new string('x', 101))
            .Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.NotEmpty(results);
        Assert.Contains(results, r => r.ErrorMessage!.Contains("cannot exceed 100"));
    }

    [Fact]
    public void NegativeBalance_FailsValidation()
    {
        // Arrange
        var transaction = new TransactionModelBuilder()
            .WithBalance(-100m)
            .Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.NotEmpty(results);
        Assert.Contains(results, r => r.ErrorMessage!.Contains("Balance must be between"));
    }

    [Fact]
    public void OptionalFieldsCanBeNull_PassesValidation()
    {
        // Arrange
        var transaction = new TransactionModelBuilder()
            .WithDescription(null)
            .WithCategory(null)
            .WithMemo(null)
            .WithCheckNumber(null)
            .WithReferenceNumber(null)
            .WithBalance(null)
            .Build();

        // Act
        var results = ValidateModel(transaction);

        // Assert
        Assert.Empty(results);
    }
}

using CrystalFinance.Ui.Enums;
using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace CrystalFinanceLibrary.Models;

public class TransactionModel
{
    [JsonPropertyName("id")]
    [Range(1, int.MaxValue, ErrorMessage = "ID must be a valid positive number.")]
    public int Id { get; set; }

    [JsonIgnore]
    public DateTime CreatedAt { get; private set; }

    [JsonPropertyName("source")]
    [Required(ErrorMessage = "Transaction source is required.")]
    public TranSourceType? Source { get; set; }

    [JsonPropertyName("trxDate")]
    [Required(ErrorMessage = "Transaction date is required.")]
    [DataType(DataType.Date)]
    [CustomValidation(typeof(TransactionModel), nameof(ValidateTransactionDate))]
    public DateTime TrxDate { get; set; }

    [JsonPropertyName("amount")]
    [Required(ErrorMessage = "Amount is required.")]
    [Range(0.01, 999999999.99, ErrorMessage = "Amount must be between 0.01 and 999,999,999.99.")]
    [DataType(DataType.Currency)]
    public decimal Amount { get; set; }

    [JsonPropertyName("description")]
    [StringLength(255, ErrorMessage = "Description cannot exceed 255 characters.")]
    public string? Description { get; set; }

    [JsonPropertyName("category")]
    [StringLength(100, ErrorMessage = "Category cannot exceed 100 characters.")]
    public string? Category { get; set; }

    [JsonPropertyName("transactionType")]
    [StringLength(50, ErrorMessage = "Transaction Type cannot exceed 50 characters.")]
    public string? TransactionType { get; set; }

    [JsonPropertyName("checkNumber")]
    [StringLength(50, ErrorMessage = "Check Number cannot exceed 50 characters.")]
    [RegularExpression(@"^\d+$", ErrorMessage = "Check Number must contain only digits.")]
    public string? CheckNumber { get; set; }

    [JsonPropertyName("referenceNumber")]
    [StringLength(50, ErrorMessage = "Reference Number cannot exceed 50 characters.")]
    public string? ReferenceNumber { get; set; }

    [JsonPropertyName("memo")]
    [StringLength(255, ErrorMessage = "Memo cannot exceed 255 characters.")]
    public string? Memo { get; set; }

    [JsonPropertyName("balance")]
    [Range(0, 999999999.99, ErrorMessage = "Balance must be between 0 and 999,999,999.99.")]
    [DataType(DataType.Currency)]
    public decimal? Balance { get; set; }

    /// <summary>
    /// Validates that transaction date is not in the future.
    /// </summary>
    public static ValidationResult? ValidateTransactionDate(DateTime trxDate, ValidationContext context)
    {
        if (trxDate.Date > DateTime.UtcNow.Date)
        {
            return new ValidationResult("Transaction date cannot be in the future.");
        }
        return ValidationResult.Success;
    }
}

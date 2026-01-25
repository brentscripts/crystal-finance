using CsvHelper.Configuration.Attributes;

namespace CrystalFinanceLibrary.Models;

public class TransactionModel
{
    [Ignore] public int Id { get; set; }
    [Ignore] public DateTime CreatedAt { get; set; }
    [Ignore] public required string Source { get; set; }

    [Name("Posting Date", "Transaction Date")]
    public DateTime TrxDate { get; set; }

    [Name("Amount")]
    public decimal Amount { get; set; }

    [Name("Description")]
    public string? Description { get; set; }

    [Name("Transaction Category", "Category")]
    public string? Category { get; set; }

    [Name("Transaction Type", "Type")]
    public string? TransactionType { get; set; }

    [Optional]
    [Name("Check Number")]
    public string? CheckNumber { get; set; }

    [Optional]
    [Name("Reference Number")]
    public string? ReferenceNumber { get; set; }

    [Optional]
    [Name("Memo")]
    public string? Memo { get; set; }

    [Optional]
    [Name("Balance")]
    public decimal? Balance { get; set; }
}

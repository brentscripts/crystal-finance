using CsvHelper.Configuration.Attributes;

namespace CrystalFinanceLibrary.Models;

public class TransactionModel
{
    [Ignore] public int Id { get; set; }
    [Ignore] public DateTime CreatedAt { get; set; }
    [Ignore] public required string Source { get; set; }

    [Name("Posting Date", "Transaction Date")]
    public DateTime TrxDate { get; set; }

    public decimal Amount { get; set; }
    public string? Description { get; set; }

    [Name("Transaction Category", "Category")]
    public string? Category { get; set; }

    [Name("Transaction Type", "Type")]
    public string? TransactionType { get; set; }

    [Name("Check Number")]
    public string? CheckNumber { get; set; }

    [Name("Reference Number")]
    public string? ReferenceNumber { get; set; }

    public string? Memo { get; set; }
    public decimal? Balance { get; set; }
}

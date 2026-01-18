

namespace CrystalFinanceLibrary.Models;

public class TransactionModel
{
    public int Id { get; set; }
    public DateTime TrxDate { get; set; }
    public decimal Amount { get; set; }
    public string? Description { get; set; }
    public string? Category { get; set; }
    public required string Source { get; set; }
    public string? TransactionType { get; set; }
    public string? CheckNumber { get; set; }
    public string? ReferenceNumber { get; set; }
    public string? Memo { get; set; }
    public decimal? Balance { get; set; }
    public DateTime CreatedAt { get; set; }
}

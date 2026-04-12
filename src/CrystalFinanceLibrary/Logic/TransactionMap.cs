using CrystalFinance.Ui.Enums;
using CrystalFinanceLibrary.Data;
using CrystalFinanceLibrary.Models;
using CsvHelper.Configuration;

namespace CrystalFinanceLibrary.Logic
{
    public sealed class TransactionMap : ClassMap<TransactionModel>
    {
        public TransactionMap()
        {
            Map(m => m.Id).Ignore();
            Map(m => m.CreatedAt).Ignore();
            Map(m => m.Source).Name("Source");
            Map(m => m.TrxDate).Name("Posting Date", "Transaction Date");
            Map(m => m.Amount).Name("Amount");
            Map(m => m.Description).Name("Description");
            Map(m => m.Category).Name("Transaction Category", "Category");
            Map(m => m.TransactionType).Name("Transaction Type", "Type");
            Map(m => m.CheckNumber).Name("Check Number").Optional();
            Map(m => m.ReferenceNumber).Name("Reference Number").Optional();
            Map(m => m.Memo).Name("Memo").Optional();
            Map(m => m.Balance).Name("Balance").Optional();
        }
    }
}

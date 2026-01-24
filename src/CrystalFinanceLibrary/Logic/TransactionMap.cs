using CsvHelper.Configuration;
using CrystalFinanceLibrary.Models;

namespace CrystalFinanceLibrary.Logic
{
    public sealed class TransactionMap : ClassMap<TransactionModel>
    {
        public TransactionMap()
        {
            Map(m => m.Id).Ignore();
            Map(m => m.CreatedAt).Ignore();
            Map(m => m.Source).Ignore();
            Map(m => m.TrxDate).Name("Posting Date", "Transaction Date");
            Map(m => m.Amount);
            Map(m => m.Description);
            Map(m => m.Category).Name("Transaction Category", "Category");
            Map(m => m.TransactionType).Name("Transaction Type", "Type");
            Map(m => m.CheckNumber).Name("Check Number");
            Map(m => m.ReferenceNumber).Name("Reference Number");
            Map(m => m.Memo);
            Map(m => m.Balance);
        }
    }
}

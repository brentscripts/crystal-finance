using CrystalFinance.Ui.Enums;
using CrystalFinanceLibrary.Models;

namespace CrystalFinance.Tests.Fixtures;

/// <summary>
/// Builder class for creating test TransactionModel instances.
/// </summary>
public class TransactionModelBuilder
{
    private int _id = 1;
    private DateTime _trxDate = DateTime.UtcNow.AddDays(-5);
    private decimal _amount = 100m;
    private string? _description = "Test Transaction";
    private string? _category = "Test Category";
    private TranSourceType? _source = TranSourceType.Bank;
    private string? _transactionType = "Debit";
    private string? _checkNumber = null;
    private string? _referenceNumber = null;
    private string? _memo = null;
    private decimal? _balance = null;

    public TransactionModelBuilder WithId(int id)
    {
        _id = id;
        return this;
    }

    public TransactionModelBuilder WithTrxDate(DateTime date)
    {
        _trxDate = date;
        return this;
    }

    public TransactionModelBuilder WithAmount(decimal amount)
    {
        _amount = amount;
        return this;
    }

    public TransactionModelBuilder WithDescription(string? description)
    {
        _description = description;
        return this;
    }

    public TransactionModelBuilder WithCategory(string? category)
    {
        _category = category;
        return this;
    }

    public TransactionModelBuilder WithSource(TranSourceType? source)
    {
        _source = source;
        return this;
    }

    public TransactionModelBuilder WithTransactionType(string? transactionType)
    {
        _transactionType = transactionType;
        return this;
    }

    public TransactionModelBuilder WithCheckNumber(string? checkNumber)
    {
        _checkNumber = checkNumber;
        return this;
    }

    public TransactionModelBuilder WithReferenceNumber(string? referenceNumber)
    {
        _referenceNumber = referenceNumber;
        return this;
    }

    public TransactionModelBuilder WithMemo(string? memo)
    {
        _memo = memo;
        return this;
    }

    public TransactionModelBuilder WithBalance(decimal? balance)
    {
        _balance = balance;
        return this;
    }

    public TransactionModel Build()
    {
        return new TransactionModel
        {
            Id = _id,
            TrxDate = _trxDate,
            Amount = _amount,
            Description = _description,
            Category = _category,
            Source = _source,
            TransactionType = _transactionType,
            CheckNumber = _checkNumber,
            ReferenceNumber = _referenceNumber,
            Memo = _memo,
            Balance = _balance
        };
    }
}

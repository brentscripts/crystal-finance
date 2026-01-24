using CrystalFinanceLibrary.Models;
using CsvHelper;
using CsvHelper.Configuration;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Threading.Tasks;

namespace CrystalFinanceLibrary.Logic;

public class TransactionImportService
{
    public async IAsyncEnumerable<TransactionModel> ImportTransactions(Stream fileStream, string source)
    {
        using var streamReader = new StreamReader(fileStream);
        using var csv = new CsvReader(streamReader, new CsvConfiguration(CultureInfo.InvariantCulture)
        {
            HasHeaderRecord = true,
            MissingFieldFound = null,
            HeaderValidated = null
        });
        csv.Context.RegisterClassMap<TransactionMap>();

        await foreach (var record in csv.GetRecordsAsync<TransactionModel>())
        {
            record.Source = source;
            yield return record;
        }
    }
}


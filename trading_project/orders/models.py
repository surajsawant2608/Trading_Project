from django.db import models

class OpenPosition(models.Model):
    user_id = models.CharField(max_length=20)
    order_id = models.CharField(max_length=30, unique=True)

    # Main status fields
    status_code = models.CharField(max_length=10, blank=True)
    order_status = models.CharField(max_length=10, blank=True)
    error_message = models.TextField(blank=True)
    text = models.TextField(blank=True)
    status = models.CharField(max_length=20, blank=True)
    orderstatus = models.CharField(max_length=20, blank=True, null=True)

    # Order information
    variety = models.CharField(max_length=20, blank=True)
    ordertype = models.CharField(max_length=20, blank=True)
    ordertag = models.CharField(max_length=50, blank=True)
    producttype = models.CharField(max_length=20, blank=True)
    transactiontype = models.CharField(max_length=10, blank=True)
    exchange = models.CharField(max_length=10, blank=True)
    duration = models.CharField(max_length=10, blank=True)

    # Symbol and instrument
    tradingsymbol = models.CharField(max_length=50, blank=True)
    symboltoken = models.CharField(max_length=10, blank=True)
    instrumenttype = models.CharField(max_length=10, blank=True)
    strikeprice = models.FloatField(default=0.0)
    optiontype = models.CharField(max_length=5, blank=True)
    expirydate = models.CharField(max_length=20, blank=True)

    # Quantity and pricing
    quantity = models.IntegerField(default=0)
    disclosedquantity = models.IntegerField(default=0)
    lotsize = models.IntegerField(default=0)
    cancelsize = models.IntegerField(default=0)
    price = models.FloatField(default=0.0)
    averageprice = models.FloatField(default=0.0)
    triggerprice = models.FloatField(default=0.0)
    squareoff = models.FloatField(default=0.0)
    stoploss = models.FloatField(default=0.0)
    trailingstoploss = models.FloatField(default=0.0)

    # Execution details
    filledshares = models.CharField(max_length=10, blank=True)
    unfilledshares = models.CharField(max_length=10, blank=True)
    fillid = models.CharField(max_length=30, blank=True)
    filltime = models.CharField(max_length=30, blank=True)

    # Timestamps
    updatetime = models.CharField(max_length=30, blank=True)
    exchtime = models.CharField(max_length=30, blank=True)
    exchorderupdatetime = models.CharField(max_length=30, blank=True)

    # Relations
    parentorderid = models.CharField(max_length=30, blank=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updatetime']

    def __str__(self):
        return f"{self.user_id} | {self.tradingsymbol} | {self.order_id}"
